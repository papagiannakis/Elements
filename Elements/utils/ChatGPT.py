import json

import openai

openai.api_key = "ENTER YOUR KEY HERE"


def replaceOps(s):
    symbols = ["*", "/", "+"]
    finished = False
    while not finished:
        symsfound = 0
        finished = True
        for sym in symbols:

            ind = s.find(sym)

            while ind != -1:
                symsfound += 1
                start = 0
                end = 0
                foundExp = ' '
                count = 1
                while True:
                    foundExp = s[ind - count]

                    if foundExp.isdigit() or foundExp == '.':
                        start = ind - count
                    else:
                        break
                    count += 1
                count = 1
                while True:
                    foundExp = s[ind + count]

                    if foundExp.isdigit() or foundExp == '.' or foundExp in symbols:
                        end = ind + count
                    else:
                        break
                    count += 1
                if start == 0:
                    s = s.replace(s[ind:end + 1], str(eval(str(360) + s[ind:end + 1])))
                else:

                    s = s.replace(s[start:end + 1], str(eval(s[start:end + 1])))
                ind = s.find(sym)
        if symsfound != 0:
            finished = False
    return s


class GPTBot:
    def __init__(self):

        self.system_prompt = """You are an expert at generating and manipulating 3d scenes. 
        - Respond in a json format with property names enclosed in double quotes
        - Don't add any additional information or examples to the output other than the scene information
        - You operate in a 3D Space. You work in a X,Y,Z coordinate system. X denotes width, Y denotes height, Z denotes depth. 
        0.0,0.0,0.0 is the default space origin
        - Keep in mind, objects should be placed in the most meaningful layout possible, and they shouldn't overlap.
        - The position refers to where the center point of the object is placed, so place objects based on their height, depth and width
        {"objectid":{"depth":0, "height":0, "width":0, "position":[0,0,0], "rotation":[0,0,0]}} 
        Where objectid is the name of the object, and it has depth, height, width and, a 3d position, rotation x,y,z.
        - Only manipulate the objects in the scene that you are asked to, don't do more than what is asked
        - Take into consideration the height, width, depth and position and rotation of each object, it's very important
        - Take into consideration our chat history too. My messages will be in format
        - Use only positive values for position and rotation, it's very important
        "role":"user","content":message
        "role":"assistant","content":message
        Where the user is me and assistant is you
        """
        self.chathistory = []
        self.scenegraph = {}

    def apicall(self, prompt):

        messages = [{"role": "system", "content": self.system_prompt}]
        inputprompt = prompt
        inputprompt += ". The current scene is " + str(
            self.scenegraph) + "."
        messages.append({"role": "user", "content": inputprompt})
        self.chathistory.append(messages[len(messages) - 1])
        # print("History:", self.chathistory)
        # print("Messages")
        # print(messages)

        correctanswer = True
        while correctanswer:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.8,
                    max_tokens=1500,
                )
                for choice in response['choices']:
                    print("Reply")
                    print(choice["message"]["content"])
                    rep = choice["message"]["content"]
                    self.chathistory.append({"role": "assistant", "content": rep})
                    firstocc = rep.find("{")
                    lastocc = rep.rfind("}")
                    rep = rep[firstocc:lastocc + 1]
                    rep = rep.replace("'", '"')
                    rep = replaceOps(rep)
                    print("Scenegraph")
                    scenegraph = json.loads(rep)
                    print(scenegraph)
                    correctanswer = False

                    self.scenegraph = scenegraph

            except:
                # del self.chathistory[-1]
                pass