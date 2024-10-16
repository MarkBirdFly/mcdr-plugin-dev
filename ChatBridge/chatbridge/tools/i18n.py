import yaml
import os
from chatbridge.common.logger import ChatBridgeLogger
word_file = "i18n.yml"

class I18n:
    def __init__(self):
        self.word_file = word_file
        self.word = {"origin":"i18n"}
        if not os.path.exists(word_file):
            with open(word_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.word, f)
        if os.path.exists(word_file):
            with open(word_file, 'r', encoding='utf-8') as f:
                self.word = yaml.safe_load(f)
        self.logger : ChatBridgeLogger
    def write_word(self):
        with open(self.word_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.word, f)
    def __call__(self, key):
        return self.word.get(key, key)
    def _update_word(self, i18n_dict):
        response = '完成更改:\n'
        removed, added, existed, updated= [],[],[],[]
        for delkey in [key for key in i18n_dict if i18n_dict[key] == None]:
            del self.word[delkey]
            del i18n_dict[delkey]
            removed.append(delkey)
        for key, value in i18n_dict.items():
            if key not in self.word:
                added.append((key, value))
            else:
                if key == self.word[key]:
                    existed.append(key)
                else:
                    updated.append((key, self.word[key], value))
        if existed:
            response += f'已存在:{existed}\n'
        if removed:
            response += f'删除了:{removed}\n'
        if added:
            added_response = ''
            for key, value in added:
                added_response += f'"{key}": "{value}"\n'
            response += f'添加了:\n{added}'
        if updated:
            updated_response = ''
            for key, org_value, value in updated:
                updated_response += f'"{key}": "{org_value}" -> "{value}"\n'
            response += f'更新了:\n{updated}'
        counts = len(removed) + len(added) + len(updated)
        if counts >1:
            response += f'完成了{counts}个更改'
        return response.strip()