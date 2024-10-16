import yaml
import os
from chatbridge.common.logger import ChatBridgeLogger
i18n_file = "i18n.yml"

class I18n:
    def __init__(self):
        self.i18n_file = i18n_file
        self.i18n = {"origin":"i18n"}
        if not os.path.exists(i18n_file):
            with open(i18n_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.i18n, f)
        if os.path.exists(i18n_file):
            with open(i18n_file, 'r', encoding='utf-8') as f:
                self.i18n = yaml.safe_load(f)
        self.logger : ChatBridgeLogger
    def write(self):
        with open(self.i18n_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.i18n, f)
    def __call__(self, key):
        return self.i18n.get(key, key)