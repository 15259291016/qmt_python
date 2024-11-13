class BTreeNode:
    def __init__(self, t, leaf=False):
        self.t = t  # 最小度数
        self.keys = []  # 节点中的键值
        self.children = []  # 子节点引用
        self.leaf = leaf  # 是否为叶子节点

    def __repr__(self):
        return f"BTreeNode(keys={self.keys}, leaf={self.leaf})"


class BTree:
    def __init__(self, t):
        self.root = BTreeNode(t, leaf=True)
        self.t = t  # 最小度数

    def search(self, k, node=None):
        # 在给定的节点中搜索键 k
        if node is None:
            node = self.root
        i = 0
        while i < len(node.keys) and k > node.keys[i]:
            i += 1
        if i < len(node.keys) and k == node.keys[i]:
            return node
        if node.leaf:
            return None
        else:
            return self.search(k, node.children[i])

    def insert(self, k):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            new_root = BTreeNode(self.t, leaf=False)
            new_root.children.append(root)
            self.split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, k)

    def split_child(self, parent, i):
        t = self.t
        node_to_split = parent.children[i]
        new_node = BTreeNode(t, node_to_split.leaf)
        parent.children.insert(i + 1, new_node)
        parent.keys.insert(i, node_to_split.keys[t - 1])

        new_node.keys = node_to_split.keys[t:(2 * t - 1)]
        node_to_split.keys = node_to_split.keys[0:t - 1]

        if not node_to_split.leaf:
            new_node.children = node_to_split.children[t:(2 * t)]
            node_to_split.children = node_to_split.children[0:t]

    def _insert_non_full(self, node, k):
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            while i >= 0 and k < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = k
        else:
            while i >= 0 and k < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.t) - 1:
                self.split_child(node, i)
                if k > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], k)

    def traverse(self, node=None):
        if node is None:
            node = self.root
        for i in range(len(node.keys)):
            if not node.leaf:
                self.traverse(node.children[i])
            print(node.keys[i], end=" ")
        if not node.leaf:
            self.traverse(node.children[len(node.keys)])


# 示例：创建一个B树并插入数据
if __name__ == "__main__":
    btree = BTree(t=2)  # 创建最小度数为2的B树
    data = [10, 20, 5, 6, 12, 30, 7, 17]

    for item in data:
        btree.insert(item)

    print("B-tree中序遍历结果:")
    btree.traverse()
    print("\n搜索键12:")
    result = btree.search(12)
    print(result)
