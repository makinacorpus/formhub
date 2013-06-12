Question = function(questionData, parent)
{
    this.name = questionData.name;
    this.type = questionData.type;
    this.label = questionData.label;
    this.parent = parent;
}

Question.prototype.getLabel = function(language)
{
    /// if plain string, return
    if(typeof(this.label) == "string")
        return this.label;
    else if(typeof(this.label) == "object")
    {
        if(language && this.label.hasOwnProperty(language))
            return this.label[language];
        else
        {
            var label = null;
            for(key in this.label)
            {
                label = this.label[key];
                break;// break at first instance and return that
            }
            return label;
        }

    }
    // return raw name
    return this.name;
}

function parseQuestions(children, prefix, cleanReplacement, tree)
{
    var idx;
    cleanReplacement = typeof cleanReplacement !== 'undefined' ? cleanReplacement : '_';
    if (tree===undefined) {
        tree = questionsTree;
    };
    for(idx in children)
    {
        var question = children[idx];
        var qid = ((prefix?prefix:'') + question.name)
        var oquestion = new Question(question, tree['question'])
        var subtree = {
            "question": oquestion,
            "jsonobj": question,
            "questions": []};
        //@TODO: do we just want to add anything with children, concern could be it item has children and is alos avalid question - if thats possible
        if(question.hasOwnProperty('children') && (question.type == "group" || question.type == "note" || question.type == "repeat"))
        {
            parseQuestions(question.children,
                qid + cleanReplacement,
                undefined, subtree);

        }
        questions[qid] = oquestion;
        // only nest repeats
        tree['questions'].push(subtree);
        if(question.type=="group" || question.type=="note"){
            $.each(subtree['questions'], function(i, itm){
                tree['questions'].push(itm);
            }
            );
            subtree['questions'] = [];
        }
    }
}


