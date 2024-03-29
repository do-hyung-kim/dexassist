import struct
NO_OFFSET = 0
NO_INDEX =  -1
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


UINT_FMT = '<I'
USHORT_FMT = '<H'
INT_FMT = '<i'
SHORT_FMT = '<h'
LONG_FMT = '<l'
ULONG_FMT = '<L'
LONGLONG_FMT = '<q'
ULONGLONG_FMT = '<Q'
DOUBLE_FMT = '<d'
FLOAT_FMT = '<f'
UBYTE_FMT = '<B'
BYTE_FMT = '<b'


ACC_PUBLIC = 0x1
ACC_PRIVATE = 0x2
ACC_PROTECTED = 0x4
ACC_STATIC = 0x8
ACC_FINAL = 0x10
ACC_SYNCHRONIZED = 0x20
ACC_SYNC = ACC_SYNCHRONIZED
ACC_VOLATILE = 0x40
ACC_BRIDGE = 0x40
ACC_TRANSIENT = 0x80
ACC_VARARGS = 0x80
ACC_NATIVE = 0x100
ACC_INTERFACE = 0x200
ACC_ABSTRACT = 0x400
ACC_STRICT = 0x800
ACC_SYNTHETIC = 0x1000
ACC_ANNOTATION = 0x2000
ACC_ENUM = 0x4000
ACC_CONSTRUCTOR = 0x10000
ACC_DECLARED_SYNCHRONIZED = 0x2000



class Dex(object):
  def __init__(self, manager):
    self.classes = []
    self.manager = manager

  def save_as(self, write_class, stream):
    p = write_class(self)
    p.write(stream)

  def add_class(self, clazz):
    self.classes.append(clazz)
  def get_class(self, clazz_type):
    for clazz in self.classes:
      if clazz.type == clazz_type: return clazz
class DexClassItem(object):
  def __init__(self):
    self.index = NO_INDEX
    self.annotations = []
    self.methods = []
    self.values = None
    # direct_methods = any of static, private, or constructor
    # virtual_methods = none of static, private, or constructor
    self.fields = []
    self.type = None
    self.name = None
    self.access_flag = 0
    self.superclass = None
    self.source_file_name = None
    self.interfaces = []
    self.static_initializers = None
    self.annotation_dir_offset = NO_OFFSET
  def __lt__(self, other):
    return str(self.type) < str(other.type)
  def __gt__(self, other):
    return str(self.type) > str(other.type)  
  
  def get_sorted_methods(self, section):
    l = self.methods
    l.sort(key = lambda x : section.get_item_index(x))
    return l
  def get_sorted_fields(self, section):
    l = self.fields
    l.sort(key = lambda x : section.get_item_index(x))
    return l
  def get_sorted_static_fields(self, section):
    l =  list(filter(lambda x : x.is_static(), self.fields))
    l.sort(key = lambda x : section.get_item_index(x))
    return l
  def get_sorted_instance_fields(self, section):
    l = list(filter(lambda x : not x.is_static(), self.fields))
    l.sort(key = lambda x : section.get_item_index(x))
    return l

  def get_sorted_direct_methods(self, section):
    l = self.get_direct_methods()
    l.sort(key = lambda x : section.get_item_index(x))
    return l

  
  def get_sorted_virtual_methods(self, section):
    l = self.get_virtual_methods()
    l.sort(key = lambda x : section.get_item_index(x))
    return l

  def get_direct_methods(self):
    return list(filter(lambda x : x.is_direct_method(), self.methods))
  
  def get_virtual_methods(self):
    return list(filter(lambda x : not x.is_direct_method(), self.methods))


  def set_name(self):
    return self.name
  def add_annotation(self, annotation):
    self.annotations.append(annotation)
  def __str__(self):
    return self.name
  def fix(self):
    pass
  def __hash__(self):
    return hash(self.name)
  def __eq__(self,othr):
    if(hash(othr) == hash(self)):
      return True
    return False

  def get_ref_strings(self):
    return self.get_related_strings()
  def get_related_strings(self):
    ret = set()
    OP_CONST_STRING = 0x1a
    ret.add(self.name)
    ret.add(self.type)
    ret.add(self.superclass)
    ret.add(self.source_file_name)
    ret.update(self.interfaces)
    for ann in self.annotations:
      ret.add(ann.type)
      for ele in ann.elements:
        ret.add(ele[0])
    for x in self.methods:
      editor = x.get_editor()
      if editor is None: continue
      for try_item in editor.tries:
        for handler in try_item.catch_handlers:
          ret.add(handler.exception_type)
      for opcode in editor.opcodes:
        if opcode.op == OP_CONST_STRING:
          ret.add(opcode.BBBB)
      for ann in x.annotations:
        ret.add(ann.type)
        for ele in ann.elements:
          ret.add(ele[0])
      for ann_list in x.param_annotations:
        if ann_list:
          for ann in ann_list:
            ret.add(ann.type)
            for ele in ann.elements:
              ret.add(ele[0])
      ret.add(x.shorty)
      ret.add(x.name)
      ret.add(x.return_type)
      ret.update(x.params)
    for x in self.fields:
      for ann in x.annotations:
        ret.add(ann.type)
        for ele in ann.elements:
          ret.add(ele[0])
      ret.add(x.type)
      ret.add(x.name)
    return ret

class DexField(object):
  def __init__(self, parent, field_name, type_name, access_flags):
    self.annotations = []
    self.name = field_name
    self.type = type_name
    self.clazz = parent
    self.access_flags = access_flags
  
  def is_static(self):
    return self.access_flags & 0x8


  def __str__(self):
    ret = '{}::{} [{}]'.format(self.clazz, self.name, self.type)
    if self.annotations:
      a = []
      for ann in self.annotations:
        a.append('@' + str(ann))
      ret += ''.join(a)
    return ret
  def __hash__(self):
    try:
      return hash(self.name + self.clazz.name)
    except:
      # for external field:
      return hash(str(self.name + self.clazz))
  def __eq__(self,othr):
    if(hash(othr) == hash(self)):
      return True
    return False
    
class DexMethod(object):
  def __init__(self, parent, method_name, access_flags, proto_shorty, parameter, return_t, editor):
    self.annotations = []
    self.name = method_name
    self.clazz = parent
    self.return_type = return_t
    self.params = parameter
    self.parameters = self.params
    self.shorty = proto_shorty
    self.make_signature()
    self.register_count = 0
    self.access_flags = access_flags
    self.param_annotations = []
    self.annotation_set_ref_list_offset = NO_OFFSET
    self.editor = editor
    self.code_item_offset = NO_OFFSET
    self.proto = DexProto(self.shorty, self.return_type, self.params)
  
  def get_instructions(self):
    if self.editor:
      return self.editor.opcodes
    return []
  def get_editor(self):
    return self.editor
  def get_try_blocks(self):
    if self.editor is None: return []
    return self.editor.tries

  def make_signature(self):
    self.signature = '{}({})'.format(self.return_type , ''.join(self.params))
    
  def create_proto(self):
    
    return self.proto

  def create_shorty_descriptor(self):
    return self.signature
  def is_direct_method(self):
    if self.is_static(): return True
    if self.is_private(): return True
    if self.is_constructor(): return True
  def is_private(self):
    return self.access_flags & ACC_PRIVATE != 0
  def is_static(self):
    return self.access_flags & ACC_STATIC != 0
  def is_constructor(self):
    return self.access_flags & ACC_CONSTRUCTOR != 0

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
    return hash(self.clazz.name + self.name + ','.join(str(x) for x in self.parameters))
  def __eq__(self,othr):
    if(hash(self) == hash(othr)):
      return True
    return False 
  
class DexProto(object):
  def __init__(self, shorty, return_type, params):
    self.shorty = shorty
    self.return_type = return_type
    self.parameters = params
  def __hash__(self):
    return hash(self.return_type + "".join(self.parameters))
  def __eq__(self,othr):
    if hash(self) == hash(othr):
      return True
    return False
  def __lt__(self, other):
    return str(self) < str(other)
  def __gt__(self, other):
    return str(self) > str(other)
  def __str__(self):
    return self.return_type + "".join(self.parameters)

class DexAnnotation(object):
  def __init__(self, target, visibility, type_name, key_name_tuples):
    self.target = target
    self.visibility = visibility
    self.type_name = type_name
    self.type = type_name
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
    return '{}({})'.format(self.type_name, self.elements)
  def __hash__(self):
    return hash(str(self))

class DexArray(object):
  def __init__(self):
    self.value_list = []
    self.ofset = NO_OFFSET
  def __hash__(self):
    ret = ""
    for s in self.value_list:
      ret += str(s)   
    return hash(ret)
  def __eq__(self, othr):
    if hash(self) == hash(othr):
      return True
    return False

class DexValue(object):
  def __init__(self, value, value_type = VALUE_TYPE_AUTO):
    self.value = value
    self.value_type = value_type
  
  def encode(self, manager, stream):
    encoded_type = self.get_type()
    encoded_value = self.value_as_byte(manager, encoded_type, stream)
    value_arg = len(encoded_value) - 1
    if encoded_type in [VALUE_TYPE_BYTE, VALUE_TYPE_ARRAY, VALUE_TYPE_ANNOTATION, VALUE_TYPE_NULL]:
      value_arg = 0
    if encoded_type == VALUE_TYPE_BOOLEAN:
      value_arg = 1 if self.value else 0

    stream.write_ubyte((((value_arg & 0xffffffff) << 5) | encoded_type))
    if encoded_type in [VALUE_TYPE_BOOLEAN, VALUE_TYPE_NULL]: return

    if encoded_type == VALUE_TYPE_ARRAY:
      stream.write_uleb(len(self.value))
      for x in self.value:
        x.encode(manager, stream)
      return

    if encoded_type == VALUE_TYPE_ANNOTATION:
      #raise Exception('do not write annotation in encode')

      stream.write_uleb(manager.type_section.get_item_index(self.value.type))
      stream.write_uleb(len(self.value.elements))
      for elem in self.value.elements:
        name = elem[0]
        val = elem[1]
        stream.write_uleb(manager.string_section.get_item_index(name))
        if isinstance(val, list):
          for x in val:
            x.encode(manager, stream)
          return
        val.encode(manager, stream)
      return

    stream.write_byte_array(encoded_value)
    #stream.position += len(encoded_value)

  def __str__(self):
    if self.get_type() in [VALUE_TYPE_ANNOTATION, VALUE_TYPE_ARRAY]:
      return format('type : {:04x}')
    return format('type : {:04x} value : {}'.format(self.get_type(), self.value))

  
  def value_as_byte(self, manager, type_value, stream):

    if type_value == VALUE_TYPE_BYTE:
      return self.write_1(self.value)
    if type_value == VALUE_TYPE_SHORT:
      return self.swrite_2(self.value)

    if type_value == VALUE_TYPE_CHAR:
      return self.write_2(self.value)

    if type_value in [VALUE_TYPE_INT, VALUE_TYPE_FLOAT]:
      return self.write_4(self.value)
    if type_value in [VALUE_TYPE_DOUBLE, VALUE_TYPE_LONG]:
      
      return self.write_8(self.value)
    if type_value == VALUE_TYPE_STRING:
      return self.write_4(manager.string_section.get_item_index(self.value))
    if type_value == VALUE_TYPE_METHOD:
      return self.write_4(manager.method_section.get_item_index(self.value))
    if type_value == VALUE_TYPE_TYPE:
      return self.write_4(manager.type_section.get_item_index(self.value))
    
    if type_value in [VALUE_TYPE_ENUM, VALUE_TYPE_FIELD]:
      return self.write_4(manager.field_section.get_item_index(self.value))

    if type_value == VALUE_TYPE_BOOLEAN:
      return bytes()
    if type_value == VALUE_TYPE_NULL:
      return bytes()
    if type_value == VALUE_TYPE_ARRAY:
      ret = bytearray()
      for item in self.value:
        ret += item.value_as_byte(manager, item.value_type, stream)
      return ret
    if type_value == VALUE_TYPE_ANNOTATION:
      return bytes() # process with encode
      
    raise Exception('0x{:04x} is not implemented'.format(type_value))
    
    # need struct.pack()
  def write_1(self, value):
    return struct.pack(UBYTE_FMT, value)
  def write_2(self, value):
    if isinstance(value, str):
      value = ord(value) # for value_type_char

    return struct.pack(USHORT_FMT, value)
  def swrite_2(self, value):
    return struct.pack(SHORT_FMT, value)
  def write_4(self, value):
    try:
      return struct.pack(UINT_FMT, value)
    except:
      return struct.pack(FLOAT_FMT, value)

  def write_8(self, value):
    try:
      return struct.pack(ULONGLONG_FMT, value)
    except:
      return struct.pack(DOUBLE_FMT, value)

  def get_type(self):
    if self.value_type == VALUE_TYPE_AUTO:
      self.value_type = self.get_inferenced_type()
    return self.value_type
  
  def get_inferenced_type(self):
    if isinstance(self.value, DexValue): return self.value.get_type()
    if self.value is None:
      return VALUE_TYPE_NULL
    if isinstance(self.value, bool):
      return VALUE_TYPE_BOOLEAN
    if isinstance(self.value, list):
      return VALUE_TYPE_ARRAY
    if isinstance(self.value, int):
      if self.value <= 0xff:
        return VALUE_TYPE_BYTE
      if -32768 <= self.value and self.value <= 32767:
        return VALUE_TYPE_SHORT
      if self.value <= 0xffffffff:
        return VALUE_TYPE_INT
      if self.value <= 0xffffffffffffffff:
        return VALUE_TYPE_LONG
    if isinstance(self.value, str):
      if len(self.value) == 1:
        return VALUE_TYPE_STRING
        #return VALUE_TYPE_CHAR
      return VALUE_TYPE_STRING
    if isinstance(self.value, float):
      return VALUE_TYPE_DOUBLE
    if isinstance(self.value, DexMethod):
      return VALUE_TYPE_METHOD
    if isinstance(self.value, DexField):
      return VALUE_TYPE_FIELD
    if isinstance(self.value, DexAnnotation):
      return VALUE_TYPE_ANNOTATION
  
    raise Exception('not treated value : {}'.format(self.value))
  def get_encoded_array_offset(self):
    return self.encoded_array_offset
  
  def set_encoded_array_offset(self,value):
    self.encoded_array_offset = value
