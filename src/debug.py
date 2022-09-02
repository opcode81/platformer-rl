import traceback
import os

class Logger(object):
    def __init__(self, enabled = True, **settings):
        self.stack = []
        self.indent = 0
        self.push(enabled, **settings)
    
    def push(self, enabled=None, **settings):
        if enabled is None: enabled = self.stack[-1][0]
        self.stack.append((enabled, settings))
        self.indent += settings.get("indent", 0)
    
    def pop(self, n=1):
        while n > 0:
            settings = self.stack.pop()[1]
            self.indent -= settings.get("indent", 0)
            n -= 1

    def __call__(self, *messages):
        enabled, settings = self.stack[-1]
        if not enabled: return
        (module, line, f, _) = traceback.extract_stack()[-2]
        print '%10s:%-5d> %s%s' % (os.path.split(module)[-1].replace(".py", ""), line, ' '*self.indent, ' '.join([str(x) for x in messages]))

log = Logger()