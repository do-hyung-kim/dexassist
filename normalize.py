NO_OFFSET = -1

class Dex(object):
  def __init__(self, manager):
    self.classes = []
    self.manager = manager

  def add_class(self, clazz):
    self.classes.append(clazz)

class DexClassItem(object):
  def __init__(self):
    self.annotations = []
    self.methods = []
    # direct_methods = any of static, private, or constructor
    # virtual_methods = none of static, private, or constructor
    self.fields = []
    self.type = None
    self.name = None
    self.access_flag = 0
    self.superclass = None
    self.source_file_name = None
    self.interfaces = []
  def set_name(self):
    return self.name
  def add_annotation(self, annotation):
    self.annotations.append(annotation)
  def __str__(self):
    return self.name
  def fix(self):
    pass
  def __hash__(self):
    return hash(self.name + self.type)
  def __eq__(self,othr):
    if(othr.hash() == self.hash()):
      return True
    return False

  def get_ref_strings(self):
    return self.get_related_strings()
  def get_related_strings(self):
    ret = set()
    OP_CONST_STRING = 0x1a
    ret.add(self.name)
    ret.add(self.type)
    for x in self.methods:
      editor = x.get_editor()
      for opcode in editor.opcodes:
        if opcode.op == OP_CONST_STRING:
          ret.add(opcode.get_string())
    for x in self.fields:
      ret.add(x.type)
    return ret

class DexField(object):
  def __init__(self, parent, field_name, type_name, access_flags):
    self.annotations = []
    self.name = field_name
    self.type = type_name
    self.clazz = parent
    self.access_flags = access_flags

  def __str__(self):
    ret = '{}::{} [{}]'.format(self.clazz, self.name, self.type)
    if self.annotations:
      a = []
      for ann in self.annotations:
        a.append('@' + str(ann))
      ret += ''.join(a)
    print(ret)
    return ret
  def __hash__(self):
    return hash(self.name + self.clazz.name)
  def __eq__(self,othr):
    if(othr.hash() == self.hash()):
      return True
    return False
    
class DexMethod(object):
  def __init__(self, parent, method_name, access_flags, proto_shorty, parameter, return_t, editor):
    self.annotations = []
    self.name = method_name
    self.clazz = parent
    self.return_type, self.params = return_t, parameter
    self.shorty = proto_shorty
    self.make_signature()
    print('signature : {}'.format(self.signature))
    self.editor = editor
  def get_editor(self):
    return self.editor

  def make_signature(self):
    self.signature = '{}({})'.format(self.return_type , ''.join(self.params))
    
  def create_proto(self):
    self.proto = DexProto(self.shorty, self.return_type, self.params)
    return self.proto

  def create_shorty_descriptor(self):
    return self.signature

  def parse_type(self, value):
    pass

  def __str__(self):
    ret = '{}::{} [{}]'.format(self.clazz, self.name, self.signature)
    if self.annotations:
      a = []
      for ann in self.annotations:
        a.append('@' + str(ann))
      ret += ''.join(a)
    opcodes = '\n'
    if self.editor:
      for x in self.editor.opcodes:
        opcodes += str(x) + '\n'
      for x in self.editor.tries:
        opcodes += str(x) + '\n'
    ret += opcodes
    return ret
  
  def __hash__(self):
    return hash(self.clazz.name + self.name + self.proto.shorty)
  def __eq__(self,othr):
    if(othr.hash() == self.hash()):
      return True
    return False 
  
class DexProto(object):
  def __init__(self, shorty, return_type, params):
    self.shorty = shorty
    self.return_type = return_type
    self.parameters = params
  def __hash__(self):
    return hash(self.shorty)
  def __eq__(self,othr):
    if self.shorty == othr.shorty:
      return True
    return False
  def __str__(self):
    return self.shorty

class DexAnnotation(object):
  def __init__(self, target, visibility, type_name, key_name_tuples):
    self.target = target
    self.visibility = visibility
    self.type_name = type_name
    self.elements = key_name_tuples
    self.annotation_offset = NO_OFFSET
    self.annotation_set_offset = NO_OFFSET
    
  def get_annotation_offset(self):
    return self.annotation_offset
  
  def set_annotation_offset(self, value):
    self.annotation_offset = value
    
  def get_annotation_set_offset(self):
    return self.annotation_set_offset
  
  def set_annotation_set_offset(self, value):
    self.annotation_set_offset = value
    
  def __str__(self):
    return '{}({})'.format(self.type_name, self.key_name_tuples)
VALUE_TYPE_BYTE = 0x00
VALUE_TYPE_SHORT = 0x02
VALUE_TYPE_CHAR = 0x03
VALUE_TYPE_INT = 0x04
VALUE_TYPE_LONG = 0x06
VALUE_TYPE_FLOAT = 0x10
VALUE_TYPE_DOUBLE = 0x11
VALUE_TYPE_METHOD_TYPE = 0x15
VALUE_TYPE_METHOD_HANDLE = 0x16
VALUE_TYPE_STRING = 0x17
VALUE_TYPE_TYPE = 0x18
VALUE_TYPE_FIELD = 0x19
VALUE_TYPE_METHOD = 0x1a
VALUE_TYPE_ENUM = 0x1b
VALUE_TYPE_ARRAY = 0x1c
VALUE_TYPE_ANNOTATION = 0x1d
VALUE_TYPE_NULL = 0x1e
VALUE_TYPE_BOOLEAN = 0x1f
VALUE_TYPE_AUTO = 0xff

class DexValue(object):
  def __init__(self, value, value_type = VALUE_TYPE_AUTO):
    self.value = value
    self.value_type = value_type
    self.encoded_array_offset = NO_OFFSET
  
  def encode(self, stream):
    encoded_type = self.get_type()
    encoded_value = self.value_as_byte(encoded_type)
    value_arg = len(encoded_value) - 1
    if encoded_type in [VALUE_TYPE_BYTE, VALUE_TYPE_ARRAY, VALUE_TYPE_ANNOTATION, VALUE_TYPE_NULL, VALUE_TYPE_BOOLEAN]:
      value_arg = 0
    stream.write_ubyte((((value_arg & 0xffffffff) << 5) | encoded_type))
    stream.wrte_byte_array(encoded_value)

  def value_as_byte(self, type_value):
    if type_value == VALUE_TYPE_BYTE:
      return write_1(self.value)
    if type_value in [VALUE_TYPE_SHORT, VALUE_TYPE_CHAR]:
      return write_2(self.value)
    # need struct.pack()
    
    return bytes()

  def write_1(self, value):
    return bytes([value & 0xff])
  def write_2(self, value):
    return bytes([value << 8 & 0xff, value & 0xff])
  def write_4(self, value):
    return bytes([value << 24 & 0xff, value << 16 & 0xff, value << 8 & 0xff, value & 0xff])
  def get_type(self):
    if self.value_type == VALUE_TYPE_AUTO:
      return self.get_inferenced_type()
    return self.value_type
  
  def get_inferenced_type(self):
    if self.value is None:
      return VALUE_TYPE_NULL
    if isinstance(self.value, bool):
      return VALUE_TYPE_BOOLEAN
    if isinstance(self.value, list):
      return VALUE_TYPE_ARRAY
    if isinstance(self.value, int):
      if self.value <= 0xff:
        return VALUE_TYPE_BYTE
      if self.value <= 0xffff:
        return VALUE_TYPE_SHORT
      if self.value <= 0xffffffff:
        return VALUE_TYPE_INT
      if self.value <= 0xffffffffffffffff:
        return VALUE_TYPE_LONG
    if isinstance(self.value, str):
      if len(self.value) == 1:
        return VALUE_TYPE_CHAR
      return VALUE_TYPE_STRING
    if isinstance(self.value, float):
      return VALUE_TYPE_DOUBLE
    if isinstance(self.value, DexMethod):
      return VALUE_TYPE_METHOD
    if isinstance(self.value, DexField):
      return VALUE_TYPE_FIELD
    if isinstance(self.value, DexAnnotation):
      return VALUE_TYPE_ANNOTATION
    
  def get_encoded_array_offset(self):
    return self.encoded_array_offset
  
  def set_encoded_array_offset(self,value):
    self.encoded_array_offset = value
