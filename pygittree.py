class PyGitTree():
    def __init__(self, name="root", value="", children=None):
        self.name = name
        self.value = value
        self.children = set()
        if children:
            for child in children:
                self.add_child(child)

    def add_child(self, node):
        self.children.add(node)

    def find(self, node):
        for child in self.children:
            if child.name == node.name:
                return child
        return None

    def contains(self, node):
        return self.find(node) != None

