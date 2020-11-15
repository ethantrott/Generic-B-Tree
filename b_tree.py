# Ethan Trott
# COS 350 - University of Maine
# Assignment 3 - Generic B-tree

import math

# a Node with a specific number of maximum children
class Node():
    # create the empty node
    def __init__(self, max_children):
        self.values = []                            # content of the node

        self.parent = None                          # pointer to parent of the node
        self.max_children = max_children            # max_children of the node
        self.children = []                          # pointers to child nodes

    # returns true if self is a leaf node
    def isLeaf(self):
        # self is a leaf node if it doesn't have any children
        return len(self.children) == 0

    # returns true if we've reached the maximum number of children
    def reachedLimit(self):
        return len(self.values) == self.max_children

    # returns the index that a specific value should be inserted into the node
    def insertPosition(self, value):
        # for each value:
        for i in range(len(self.values)):
            # if the new value is less than it:
            if value < self.values[i]:
                # insert here
                return i
        
        # if no larger value is found, insert at the end
        return len(self.values)

    # splits the node into two nodes
    def split(self):
        # get the index of the middle value
        midValue = math.ceil(len(self.values) / 2) - 1

        # new nodes
        first = Node(self.max_children)
        second = Node(self.max_children)

        # split the values between the new nodes
        first.values = self.values[0:midValue]
        second.values = self.values[midValue + 1:]

        # split the children between the new nodes
        first.children = self.children[0:midValue + 1]
        second.children = self.children[midValue + 1:]

        # remap the parents of the children to the new parents
        for child in first.children:
            child.parent = first
        for child in second.children:
            child.parent = second

        # get the value (the middle) being moved up to the parent (or new root)
        moveUp = self.values[midValue]

        # if we have a parent:
        if self.parent != None:
            # get the position to insert the middle value into the parent
            insertPosition = self.parent.insertPosition(moveUp)

            # insert the middle value in the parent at the correct position
            self.parent.values.insert(insertPosition, moveUp)

            # make the left-most new node the child of the middle value
            self.parent.children[insertPosition] = first

            # if we can, make the right-most new node a child at the next position (and move the rest to the right)
            if insertPosition + 1 <= len(self.parent.children) - 1:
                self.parent.children.insert(insertPosition + 1, second)

            # if the position doesn't exist, increase the size of the list and add it
            else:
                self.parent.children.append(second)

            # assign new nodes' shared parent
            first.parent = self.parent
            second.parent = self.parent

            # return the parent
            return self.parent

        # if we don't have a parent (this is the root), moveUp will become the new root
        else:
            # create the new root
            newRoot = Node(self.max_children)

            # add the new nodes as children
            newRoot.children.append(first)
            newRoot.children.append(second)

            # moveUp will be the only value
            newRoot.values.append(moveUp)

            # assign the new root as the new nodes' shared parent
            first.parent = newRoot
            second.parent = newRoot

            # return the root
            return newRoot

    def inorder(self, sorted=None):
        # if we haven't created the sorted list object yet, do so now
        if sorted == None:
            sorted = []

        for i in range(len(self.values)):
            # add smaller child values to the list if there are any
            if (i <= len(self.children) - 1) and (self.children[i] is not None):
                self.children[i].inorder(sorted)

            # add this value to the list
            sorted.append(self.values[i])

            # if this is the last value, add larger child values if there are any
            if i == len(self.values)-1:
                if (i+1 <= len(self.children) - 1) and (self.children[i+1] is not None):
                    self.children[i+1].inorder(sorted)
        
        return sorted
        

# a general b-tree, parameterized with the maximum number of children
class BTree():
    def __init__(self, max_children):
        self.max_children = max_children
        self.root = Node(self.max_children)
        self.disk_reads = 0
        self.disk_writes = 0

        self.DiskWrite()

    # increment disk_reads counter
    def DiskRead(self):
        self.disk_reads += 1
    
    # incrament disk_writes counter
    def DiskWrite(self):
        self.disk_writes += 1

    # to get inorder traversal of tree, call inorder on the root
    def inorder(self):
        return self.root.inorder()

    # insert a data member into the tree
    def insert(self, data):
        # get the leaf to insert the data
        node = self.getLeaf(data)

        # get the current values in the leaf
        values = node.values

        # if the leaf is empty, just add the element
        if len(values) == 0:
            values.append(data)

        # if the leaf is not empty:
        else:
            # get the position to insert
            position = 0
            while position < len(node.values):
                if data < node.values[position]:
                    break
                position += 1

            # insert at that position
            values.insert(position, data)

            # check if the node is full
            self.checkForSplit(node)
        
        self.DiskWrite()

    # for a list, just insert the elements one at a time
    def insert_list(self, data):
        for i in range(len(data)):
            self.insert(data[i])

    # recursively search for a data value in the tree, starting from the root (or node)
    def search(self, data, node=None):
        # if no start point specified, search from the root
        if node == None:
            node = self.root

        position = 0
        # for each value in the node:
        while position < len(node.values):
            value = node.values[position]
            self.DiskRead()

            # if the value is what we're looking for, let the user know
            if value == data:
                print("Item found.")
                result = dict()
                result['node'] = node
                result['position'] = position
                return result
            
            # if the value is greater then we've gone too far, continue to check the next child
            elif value > data:
                break

            # otherwise, check the next position
            else:
                position += 1

        # if we haven't found it, if the node isn't a leaf, keep searching from the child
        if not node.isLeaf():
            return self.search(data, node.children[position])
        
        #if we haven't found it and the node is a leaf, the item is not in the tree
        else:
            print('Cannot find value '+str(data)+'.')
            return -1

    # delete a node with that contains data, if it exists
    def delete(self, data):
        # search for the element
        search_result = self.search(data)

        # if the element is in the tree, delete
        if search_result is not -1:
            # get the node and posion from the search result
            node = search_result['node']
            position = search_result['position']

            # if the value is in a leaf:
            if node.isLeaf():
                # delete the value from the node
                node.values.pop(position)

                # if there are no values left, start a merge
                if len(node.values) == 0:
                    self.merge(node)
            
            # if the value is in a non-leaf node, replace it with the largest smaller element in the tree
            else:
                # get the closest leaf
                closestLeaf = self.getLeaf(data, node)

                # get the largest value in that leaf and remove it
                largestChoice = closestLeaf.values.pop()

                # put that value in the position of the now deleted value
                node.values[position] = largestChoice

                # if the leaf is now empty, start a merge
                if len(closestLeaf.values) == 0:
                    self.merge(closestLeaf)

            print("Item deleted.")
            self.DiskWrite()
            
    # start a merge on an empty node
    def merge(self, node):
        pointer = None                          # the index of the parent's pointer to this node
        parent = node.parent                    # the parent

        # if this isn't the root, get the parent's pointer to this node
        if parent is not None:
            position = 0
            # for each of our parent's children:
            while position < len(parent.children):
                # if we are this child, set the pointer index
                if parent.children[position] == node:
                    pointer = position
                position += 1

        #if we're the first child:
        if pointer == 0:
            # get the right child
            right = True
            sister = parent.children[1]
        else:
            # get the left child
            right = False
            sister = parent.children[pointer - 1]

        self.DiskRead()

        # if the sister has multiple values, steal one
        if len(sister.values) > 1:
            # if this is the right sister, take the smallest value
            if right:
                sisterValue = sister.values.pop(0)
                parentValue = parent.values[pointer]

            # if this is the left sister, take the larger value
            else:
                sisterValue = sister.values.pop()
                parentValue = parent.values[pointer - 1]
                
            # add the parent's value to this node
            node.values.append(parentValue)

            # if this is a large value add it to the end
            if right:
                parent.values[pointer] = sisterValue

            # if this is a smaller value add it to the front
            else:
                parent.values[pointer - 1] = sisterValue

        # if the sister doesn't have multiple values, merge
        else:
            # if this is the right sister, take the parent's larger value
            if right:
                # get the largest value
                parentValue = parent.values.pop(pointer)

                # add the value to this node
                node.values.append(parentValue)

                # merge this and sister's values
                node.values = node.values + sister.values

                # merge this and sister's children
                node.children = node.children + sister.children

                # remove sister
                parent.children.pop(pointer + 1)

            # if this is the left sister, take parent's smaller value
            else:
                # get the smaller value
                parentValue = parent.values.pop(pointer - 1)

                # copy sister's values to this node
                node.values = sister.values.copy()

                # add the parent's value to this node
                node.values.append(parentValue)

                # temporarily store children
                temp = node.children.copy()

                # get sisters children
                node.children = sister.children.copy()

                # combine the two
                node.children = node.children + temp

                # this is now the only sibling
                parent.children[pointer - 1] = node

                # remove the old pointer
                parent.children.pop(pointer)

                self.DiskWrite()

            #  if the parent is now empty, continue merging
            if len(parent.values) == 0:
                # if the parent was not the root, continue merging
                if parent.parent != None:
                    self.merge(parent)

                # if the parent was the root, just make the merged node the root instead
                else:
                    node.parent = None
                    self.root = node

    # do a split if the node is full
    def checkForSplit(self, node):
        # while we have maximum occupany
        while node.reachedLimit():
            # split the node and get the parent
            node = node.split()

            for _ in range(3):
                self.DiskWrite()

            # if the parent is the root, assign it as such
            if node.parent == None:
                self.root = node

    # returns a leaf below the provided node (or root)
    def getLeaf(self, data, node=None):
        # if no node given, get leaf from root
        if node == None:
            node = self.root
        
        # find the position where the node would be inserted
        position = 0
        while position <= len(node.values)-1:
            self.DiskRead()
            if node.values[position] > data:
                break
            else:
                position += 1

        # if the node is not a leaf, call recursively on the child
        if not node.isLeaf():
            return self.getLeaf(data, node.children[position])
        
        #if the node is a leaf, return itself
        else:
            return node
