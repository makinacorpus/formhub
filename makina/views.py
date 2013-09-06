#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import copy
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
import os
import json
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage, get_storage_class
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound,\
    HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST,\
    require_http_methods
from guardian.shortcuts import assign, remove_perm, get_users_with_perms

from main.forms import UserProfileForm, FormLicenseForm, DataLicenseForm,\
    SupportDocForm, QuickConverterFile, QuickConverterURL, QuickConverter,\
    SourceForm, PermissionForm, MediaForm, MapboxLayerForm, \
    ActivateSMSSupportFom
from odk_logger.models import Instance, XForm
from odk_logger.views import enter_data
from odk_viewer.models import DataDictionary, ParsedInstance
from odk_viewer.models.data_dictionary import upload_to
from odk_viewer.models.parsed_instance import GLOBAL_SUBMISSION_STATS,\
    DATETIME_FORMAT
from odk_viewer.views import survey_responses, attachment_url
from stats.models import StatsCount
from stats.tasks import stat_log
from utils.decorators import is_owner
from utils.logger_tools import response_with_mimetype_and_name, publish_form
from utils.user_auth import (
    set_profile_data,
    has_permission, helper_auth_helper, get_xform_and_perms,
    add_cors_headers,
    check_and_set_user,
    check_and_set_user_and_form,
)


from pyxform.question import Question

from collections import OrderedDict

#from djgeojson.http import HttpJSONResponse
#from djgeojson.serializers import Serializer as GeoJSONSerializer
#from djgeojson import GEOJSON_DEFAULT_SRID


def noauth_check_and_set_user(request, username):
    content_user = None
    try:
        content_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseRedirect("/")
    return content_user


def noauth_check_and_set_user_and_form(username, id_string, request):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    return [xform, owner]

@require_http_methods(["GET", "OPTIONS"])
def geojson(request, username=None, id_string=None):
    """
    Return form instances (records) as GeoJson
    Points Collection.
    """
    if request.method == "OPTIONS":
        response = HttpResponse()
        add_cors_headers(response)
        return response
    helper_auth_helper(request)
    xform, owner = check_and_set_user_and_form(username, id_string, request)

    if not xform:
        return HttpResponseForbidden(_(u'Not shared.'))
    try:
        args = {
            'username': username,
            'id_string': id_string,
            'query': request.GET.get('query'),
            'fields': request.GET.get('fields'),
            'sort': request.GET.get('sort')
        }
        if 'start' in request.GET:
            args["start"] = int(request.GET.get('start'))
        if 'limit' in request.GET:
            args["limit"] = int(request.GET.get('limit'))
        if 'count' in request.GET:
            args["count"] = True if int(request.GET.get('count')) > 0\
                else False
        cursor = ParsedInstance.query_mongo(**args)
    except ValueError, e:
        return HttpResponseBadRequest(e.__str__())
    records = list(record for record in cursor)
    datad = xform.data_dictionary()
    odata = dict([
        (dd, aa) for dd, aa in
        [(d, datad.get_element(d))
         for d in datad.get_headers(include_additional_headers=True)]
         if isinstance(aa, Question) or aa is None
    ])
    res = []
    proj="900913"
    proj="google-projection"
    proj="3785"
    proj="3857"
    crs = {
        "type": "link",
        "properties": {
            "href": "http://spatialreference.org/ref/epsg/%s/" % proj,
            "type": "proj4",
        }
    }
    crs = {
        "type": "EPSG",
        "code": proj,
    }
    top = {
        #"crs": crs,
        "type":  "FeatureCollection",
        "features": [],
        "properties": OrderedDict(),
    }
    top['properties']['name'] =id_string
    featuret = {
        #"crs": crs,
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-1, -1],
        },
    }
    def sortdata(item):
        i = 1
        if item[0] in ['_geolocation']:
            i = 2
        return i, item[0], item[1]
    def sort_keys(item):
        base = item[0]
        key = base
        pref = ''
        if key in ['geoloc_type']:
            pref += '0500'
        elif key.startswith('links/'):
            pref += '1000'
        elif key in ['start']:
            pref += '3000'
        elif key in ['today']:
            pref += '3500'
        elif key in ['end']:
            pref += '4000'
        elif key.startswith('_'):
            pref += '6000'
        else:
            pref += '5000'
        return pref+'_'+key
    for i, record in enumerate(records[:]):
        points = OrderedDict()
        locs = []
        ddrecord = records[i]
        robj = copy.deepcopy(record)
        rdata = robj.items()
        # put some fields at end to let other ones override !
        rdata.sort(key=sortdata)
        for k, data in rdata:
            question = odata.get(k, None)
            if ((question and question.type == 'geopoint')
                or k in [
                    u'_geolocation',
                    '_geolocation']):
                if isinstance(data, basestring):
                    data = data.split()
                if (
                    isinstance(data, (tuple, list))
                    and (len(data) > 1)
                    and (not None in data)):
                    point = (float(data[1]), float(data[0]))
                    if point not in points.values():
                        points[k] = point
                del ddrecord[k]
            if question is None:
                delete = False
                for end in [
                    '_loc_latitude',
                    '_loc_longitude',
                    '_loc_precision',
                ]:
                    if k.endswith(end):
                        delete = True
                if k in [u'_attachments']:
                    delete = True
                if delete:
                    del ddrecord[k]
        for idg, p in points.items():
            feature = copy.deepcopy(featuret)
            feature["geometry"]["coordinates"] = p
            feature["properties"] = OrderedDict()
            feature["properties"] = OrderedDict()
            datas = ddrecord.items()
            datas.append(("geoloc_type", idg))
            fburl = reverse(
                'main.views.show',
                kwargs = {
                    'username': username,
                    'id_string': record['_xform_id_string'],
                })
            burl = reverse(
                'odk_viewer.views.instance',
                kwargs = {
                    'username': username,
                    'id_string': record['_xform_id_string'],
                })
            buri = request.build_absolute_uri(burl)
            fburi = request.build_absolute_uri(fburl)
            datas.append(("links/formhub/view/form", fburi))
            datas.append(("links/formhub/view/instance",
                buri + '#/%s' % record['_id']))
            datas.sort(key=sort_keys)
            for k, data in datas:
                feature['properties'][k] = data
            top['features'].append(feature)
    response = HttpResponse()
    response['Content-Type'] = 'application/json'
    response['Content-Description'] = 'File Transfer'
    response['Content-Disposition'] = (
        'attachment; name=%s.geojson; filename=%s.geojson' % (
            record['_xform_id_string'],
            record['_xform_id_string'],
        )
    )
    data = json.dumps(top, separators=(',',': '), indent=4,)
    response.write(data)
    return response


# vim:set et sts=4 ts=4 tw=80:
