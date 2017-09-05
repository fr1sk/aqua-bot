

#Number of buttons limited to 3 for a single message or a generic message per element

def create_buttons(type,title,payload=None,url=None):
    try:
        button_dic = {}
        button_dic["type"]=type
        button_dic["title"]=title
        button_dic["payload"]=payload
        button_dic["url"] = url
        return button_dic
    except Exception as e:
        print e
        pass
