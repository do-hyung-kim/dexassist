import dexassist.bytecodes.base as base
import dexassist.dex.dex as dex


"""
this class can modify dex opcodes.
```
editor = method.get_editor()
for opcode in editor.opcodes:
  if opcode.op == CONST_STRING:
    opcode.string = opcode.string + ' update'
  if opcode.op == INVOKE_DYNAMIC:
    opcode.method = new_method
```
"""
class Editor(object):
  def find_label(self, name):
    for x in self.labels:
      if x.name == name: return x
    return None

  def remove(self, opcode):
    index = self.opcode_list.index(opcode)
    if index != -1:
      self.opcode_list.remove(opcode)
      nop = base.Instruction10x(dex.DexManager())
      nop.op = 0
      nop.high = 0
      for i in range(opcode.get_code_unit_count()):
        self.opcode_list.insert(index + i, nop)

      
  @property
  def unique_key(self):
    self.__unique_key += 1
    return self.__unique_key
  def __init__(self):
    """
      Parameters
        virtualized opcode list
      initialize editor instance
    """

    self.tries = []
    self.opcode_list = []
    self.labels = []
    self.__unique_key = 0
    for x in self.opcodes:
      x.unique_key = self.unique_key


  def commit(self):
    """
      commit all changed.
      changes will not affected after commit() calls.
      call in dexwriter
    """
    pass

  def save(self):
    """
      alternative commit()
      ```
        def save(self):
          self.commit()
      ```
    """
    self.commit()


  @property
  def opcodes(self):
    """
      opcode iterator
    """
    return self.opcode_list

  def is_in_try(self, opcode):
    offset = self.get_opcode_offset(opcode)
    for t in self.tries:
      if t.is_in(offset):
        return t
    return None
  def get_opcode_offset(self, opcode):
    """
      return current opcode offset
      return -1 if opcode does not exist in opcodes
    """
    i = 0
    for x in self.opcodes:
      if x.unique_key == opcode.unique_key:
        return i
      i += len(x)
    return -1


"""
try-catch class.
"""
class TryCatch(object):
  def __init__(self, editor, start, end, catch_handlers, catch_all_handlers):
    self.editor = editor
    self.start = start
    self.end = end
    self.catch_handlers = catch_handlers
    self.catch_all_handlers = catch_all_handlers
  def __str__(self):
    return '{} {} {}'.format(self.start, self.end, self.catch_all_handlers)
  def is_in(self, opcode):
    if isinstance(opcode, int):
      offset = opcode
    else:
      offset = self.editor.get_opcode_offset(opcode)

    start_offset = self.editor.get_opcode_offset(self.start)
    end_offset = self.editor.get_opcode_offset(self.end)
    return offset >= start_offset and offset <= end_offset

  def get_exception_handlers(self):
    return self.catch_handlers

  def get_start_addr(self): ##offset item set needed
    return self.start

  def get_code_count(self): ## this needs calculation in code_writer
    return self.end - self.start + 1
    

  

"""
virtual opcode class.
make compatable with dex opcode <-> editor opcode.
compat layer class of smali/dex opcode.
this class will be assume same interface between dex/smali
"""
class VopCode(object):
  def __init__(self, op):
    self.op = op


"""
target offset class
if opcode has target branch offset, target branch offset will be replaced with label class.
"""
class Label(object):
  def __init__(self, editor, op, name=None):
    self.op = op
    op.labeled = True
    self.editor = editor
    self.name = name
    self.editor.register_label(self)
  
  def get_offset(self):
    return self.editor.get_opcode_offset(self.op)


"""
```
label = editor.get_label_by_name("test_label")
opcode = editor.get_opcode_by_offset(68)
if opcode 
```
"""

class DexHandlerTypeAddr(object):
  def __init__(self, type_, addr):
    self.exception_type = type_
    self.addr = addr
  def get_handler_addr(self):
    return self.addr
  def get_exception_type(self):
    return self.exception_type
  def __str__(self):
    return str(self.exception_type)