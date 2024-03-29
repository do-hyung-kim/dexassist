import struct
try:
  from dexassist.writer.multidex.multidex import DefaultMultiDexPolicy
  from dexassist.writer.dex.section import *
except:
  from .multidex import multidex
  from .section import *

from .util import InstructionUtil

from .stream import OutputStream
from .stream import TempOutputStream
from .stream import InstructionWriter
from dexassist.normalize import DexValue, DexMethod, DexField
import hashlib
import zlib

NO_INDEX = -1
NO_OFFSET = 0

INSTRUCT_TYPE_METHOD = 2

LITTLE_ENDIAN_TAG = 0x12345678
# item type
HEADER_ITEM = 0x0000
STRING_ID_ITEM = 0x0001
TYPE_ID_ITEM = 0x0002
PROTO_ID_ITEM = 0x0003
FIELD_ID_ITEM = 0x0004
METHOD_ID_ITEM = 0x0005
CLASS_DEF_ITEM = 0x0006
CALL_SITE_ID_ITEM = 0x0007
METHOD_HANDLE_ITEM = 0x0008
MAP_LIST = 0x1000
TYPE_LIST = 0x1001
ANNOTATION_SET_REF_LIST = 0x1002
ANNOTATION_SET_ITEM = 0x1003
CLASS_DATA_ITEM = 0x2000
CODE_ITEM = 0x2001
STRING_DATA_ITEM = 0x2002
DEBUG_INFO_ITEM = 0x2003
ANNOTATION_ITEM = 0x2004
ENCODED_ARRAY_ITEM = 0x2005
ANNOTATION_DIRECTORY_ITEM = 0x2006
HIDDENAPI_CLASS_DATA_ITEM = 0xf000


SIZE_CLASS_DEF_ITEM = 32
SIZE_HEADER_ITEM = 112
SIZE_MAP_ITEM = 12
SIZE_MEMBER_ID_ITEM = 8
SIZE_PROTO_ID_ITEM = 12
SIZE_SIGNATURE = 20
SIZE_STRING_ID_ITEM = 4
SIZE_TRY_ITEM = 8
SIZE_TYPE_ID_ITEM = 4
SIZE_TYPE_ITEM = 2
SIZE_UBYTE = 1
SIZE_UINT = 4
SIZE_USHORT = 2


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


STRING_ID_ITEM_SIZE = 4
TYPE_ID_ITEM_SIZE = 4
PROTO_ID_ITEM_SIZE = 4 + 4 + 4
FIELD_ID_ITEM_SIZE = 2 + 2 + 4
METHOD_ID_ITEM_SIZE = 2 + 2 + 4
CLASS_DEF_ITEM_SIZE = 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4
CALL_SITE_ID_ITEM_SIZE = 4
METHOD_HANDLE_ITEM_SIZE = 2 + 2 + 2 + 2


INSTRUCT_TYPE_STRING = 0
INSTRUCT_TYPE_TYPE = 1
INSTRUCT_TYPE_METHOD = 2
INSTRUCT_TYPE_FIELD = 3
INSTRUCT_TYPE_OFFSET = 4
INSTRUCT_TYPE_KIND = 5
INSTRUCT_TYPE_PROTO = 6

# for odex
INSTRUCT_TYPE_CALL_SITE = 7
INSTRUCT_TYPE_METHOD_HANDLE = 8
INSTRUCT_TYPE_CALL_METHOD = 9
INSTRUCT_TYPE_CALL_PROTO = 10

def get_method_register_count(method):
  return get_parameter_register_count(method.parameters, method.is_static())
  
def get_parameter_register_count(parameters, is_static):

  reg_count = 0
  #print('calc param register count for {}'.format(parameters))
  for param_type in parameters:
    reg_count += 1
    if param_type[0] in ['J', 'D']:
      reg_count += 1

  if not is_static: reg_count += 1
  #print('return reg_count is {}, is_static is {}'.format(reg_count, is_static))
  return reg_count

class SectionManager(object):
  @property
  def proto_section(self):
    return self.get_section(SECTION_PROTO)

  @property
  def type_section(self):
    return self.get_section(SECTION_TYPE)
  @property
  def field_section(self):
    return self.get_section(SECTION_FIELD)
  @property
  def method_section(self):
    return self.get_section(SECTION_METHOD)
  @property
  def string_section(self):
    return self.get_section(SECTION_STRING)
  def __init__(self, manager):
    self.section_map = {
      SECTION_STRING: StringSection(self),
      SECTION_TYPE: TypeSection(self),
      SECTION_PROTO: ProtoSection(self),
      SECTION_ANNOTATION_SET: AnnotationSetSection(self),
      SECTION_ANNOTATION: AnnotationSection(self),
      SECTION_CLASS: ClassSection(self),
      SECTION_ENCODED_ARRAY: EncodedArraySection(self),
      SECTION_FIELD: FieldSection(self),
      SECTION_METHOD: MethodSection(self),
      SECTION_METHOD_HANDLE: MethodHandleSection(self),
      SECTION_CALL_SITE: CallSiteSection(self),
      SECTION_TYPE_LIST: TypeListSection(self)
    }
    self.externel_manager = manager
  def get_section(self, key):
    return self.section_map[key]

  def add_encoded_value(self, value):
    if isinstance(value, list):
      for v in value:
        self.add_encoded_value(v)
    
    if not isinstance(value, DexValue):
      item = DexValue(value)
      return self.add_encoded_value(item)

    elif value.get_type() == VALUE_TYPE_ARRAY:
      for v in value.value:
        self.add_encoded_value(v)
    elif value.get_type() == VALUE_TYPE_ANNOTATION:
      self.get_section(SECTION_TYPE).add_item(value.value.type)
      self.get_section(SECTION_STRING).add_item(value.value.type)
      for elem in value.value.elements:
        self.get_section(SECTION_STRING).add_item(elem[0])
        self.add_encoded_value(elem[1])
    elif value.get_type() == VALUE_TYPE_STRING:
      self.get_section(SECTION_STRING).add_item(value.value)
    elif value.get_type() == VALUE_TYPE_TYPE:
      self.get_section(SECTION_TYPE).add_item(value.value)
      self.get_section(SECTION_STRING).add_item(value.value)
    elif value.get_type() == VALUE_TYPE_ENUM or value.get_type() == VALUE_TYPE_FIELD:
      self.get_section(SECTION_FIELD).add_item(value.value)
      self.get_section(SECTION_TYPE).add_item(value.value.type)
      self.get_section(SECTION_TYPE).add_item(value.value.clazz) # for external field
      self.get_section(SECTION_STRING).add_item(value.value.type)
      self.get_section(SECTION_STRING).add_item(value.value.clazz) 
    elif value.get_type() == VALUE_TYPE_METHOD:
      self.get_section(SECTION_METHOD).add_item(value.value)
    elif value.get_type() == VALUE_TYPE_METHOD_HANDLE:
      raise Exception("Method Handle is not supported")
      self.get_section(SECTION_METHOD_HANDLE).add_item(value.value)
    elif value.get_type() == VALUE_TYPE_METHOD_TYPE:
      self.get_section(SECTION_PROTO).add_item(value.value.get_protos())

  def build_string_section(self, dex_pool):
    x = set()
    section = self.get_section(SECTION_STRING)
    for clazz in dex_pool:
      p = clazz.get_related_strings()
      x.update(p)
    for string_ in self.externel_manager.externel_string_list:
      x.add(string_)
    if None in x:
      x.remove(None)
    x = list(x)
    x.sort()
    for strings in x:
      section.add_item(strings)

  def build_type_section(self, dex_pool):
    section = self.get_section(SECTION_TYPE)
    str_section = self.get_section(SECTION_STRING)
    type_list = set()
    for clazz in dex_pool:
      type_list.add(clazz.type)
      type_list.update(clazz.interfaces)
      
      for field in clazz.fields:
        type_list.add(field.type)
        for ann in field.annotations:
          type_list.add(ann.type)

      for method in clazz.methods:
        type_list.add(method.return_type)
        for parameter in method.params:
          type_list.add(parameter)
        for ann in method.annotations:
          type_list.add(ann.type)
        if method.param_annotations:
          for ann_list in method.param_annotations:
            if ann_list:
              for ann in ann_list:
                type_list.add(ann.type)
      for ann in clazz.annotations:
        type_list.add(ann.type)

    for type_ in self.externel_manager.externel_type_list:
      type_list.add(type_)
    x = list(type_list)
    x.sort()
    for types in x:
      section.add_item(types)
      str_section.add_item(types)

  def build_proto_section(self, dex_pool):
    section = self.get_section(SECTION_PROTO)
    string_section = self.get_section(SECTION_STRING)
    proto_list = set()
    for clazz in dex_pool:
      for method in clazz.methods:
        proto_list.add(method.proto)
    for proto_ in self.externel_manager.externel_proto_list:
      proto_list.add(proto_)
      
    
    x = list(proto_list)
    for protos in x:
      section.add_item(protos)
      string_section.add_item(protos.shorty)
      string_section.add_item(protos.return_type)
      for param in protos.parameters:
        string_section.add_item(param)
  def build_field_section(self, dex_pool):
    section = self.get_section(SECTION_FIELD)
    field_list = set()
    for clazz in dex_pool:
      for field in clazz.fields:
        field_list.add(field)
    for field_ in self.externel_manager.externel_field_list:
      field_list.add(field_)
    x = list(field_list)
    initial_values = []
    for field in x:
      section.add_item(field)

      if field.annotations:
        self.get_section(SECTION_ANNOTATION_SET).add_item(field.annotations)

  
  def build_method_section(self, dex_pool):
    section = self.get_section(SECTION_METHOD)
    method_list = set()
    for clazz in dex_pool:
      for method in clazz.methods:
        method_list.add(method)
    for method_ in self.externel_manager.externel_method_list:
      method_list.add(method_)
    x = list(method_list)
    for method in x:
      section.add_item(method)
      self.build_code_item_section(method)
      self.build_debug_info_item_section(method)
      if method.annotations:
        #print('add method annotations! key : {}'.format(self.get_section(SECTION_ANNOTATION_SET).hash(method.annotations)))
        self.get_section(SECTION_ANNOTATION_SET).add_item(method.annotations)
      if method.param_annotations:
        for ann in method.param_annotations:
          self.get_section(SECTION_ANNOTATION_SET).add_item(ann)


  def get_data_section_offset(self):
    ret = 0x70 # header_item_size
    ret += self.get_section(SECTION_STRING).get_item_count() * STRING_ID_ITEM_SIZE
    ret += self.get_section(SECTION_TYPE).get_item_count() * TYPE_ID_ITEM_SIZE
    ret += self.get_section(SECTION_PROTO).get_item_count() * PROTO_ID_ITEM_SIZE
    ret += self.get_section(SECTION_FIELD).get_item_count() * FIELD_ID_ITEM_SIZE
    ret += self.get_section(SECTION_METHOD).get_item_count() * METHOD_ID_ITEM_SIZE
    ret += self.get_section(SECTION_CLASS).get_item_count() * CLASS_DEF_ITEM_SIZE
    ret += self.get_section(SECTION_CALL_SITE).get_item_count() * CALL_SITE_ID_ITEM_SIZE
    ret += self.get_section(SECTION_METHOD_HANDLE).get_item_count() * METHOD_HANDLE_ITEM_SIZE
    return ret
  
  def build_class_def_section(self, dex_pool):
    section = self.get_section(SECTION_CLASS)
    clazz_list = set()
    for clazz in dex_pool:
      clazz_list.add(clazz)
    for clazz in clazz_list:
      section.add_item(clazz)
      #if clazz.annotations:
        #self.get_section(SECTION_ANNOTATION_SET).add_item(clazz.annotations)
      #self.get_section(SECTION_ENCODED_ARRAY).add_item(clazz.values)
      if clazz.annotations:
        self.get_section(SECTION_ANNOTATION_SET).add_item(clazz.annotations)
      if clazz.static_initializers:
        self.get_section(SECTION_ENCODED_ARRAY).add_item(clazz.static_initializers)

  def build_call_site_id_section(self, dex_pool): # pass, for reflection
    pass

  def build_method_handle_section(self, dex_pool): # pass, for reflection
    pass

  def build_map_list_section(self, dex_pool):
    pass

  def build_type_list_section(self, dex_pool):
    section = self.get_section(SECTION_TYPE_LIST)
    clazz_list = set()
    for clazz in dex_pool:
      section.add_item(clazz.interfaces)
      for method in clazz.methods:
        section.add_item(method.proto.parameters)

    for type_list_ in self.externel_manager.externel_type_list_list:
      section.add_item(type_list_)



  def build_code_item_section(self, method):
    if method.get_editor() == 0: return
    if method.get_editor() is None: return

    for code in method.get_editor().opcode_list:  
      item = code.get_item()
      if code.op == 0xfb:
        self.get_section(SECTION_METHOD).add_item(item[0])
        self.get_section(SECTION_PROTO).add_item(item[1])
      elif code.ref_type == INSTRUCT_TYPE_STRING:
        self.get_section(SECTION_STRING).add_item(item)
      elif code.ref_type == INSTRUCT_TYPE_TYPE:
        self.get_section(SECTION_TYPE).add_item(item)
        self.get_section(SECTION_STRING).add_item(item)
      elif code.ref_type == INSTRUCT_TYPE_FIELD:
        self.get_section(SECTION_FIELD).add_item(item)
      elif code.ref_type == INSTRUCT_TYPE_METHOD:
        self.get_section(SECTION_METHOD).add_item(item)
      elif code.ref_type == INSTRUCT_TYPE_CALL_SITE:
        self.get_section(SECTION_CALL_SITE).add_item(item)
        
    tries = method.get_try_blocks()
    for tryblock in tries:
      for handler in tryblock.catch_handlers:
        if handler.exception_type:
          self.get_section(SECTION_TYPE).add_item(handler.exception_type)
          self.get_section(SECTION_STRING).add_item(handler.exception_type)

    



  def build_debug_info_item_section(self, method):
    pass




  def build_hiddenapi_class_data_item_section(self, dex_pool): # pass, for reflection
    pass
  

class DexWriter(object):
  def __init__(self, dex_class_pool):
    self.manager = SectionManager(dex_class_pool.manager)
    self.dex_class_pool = dex_class_pool
    self.multidex_policy = multidex.DefaultMultiDexPolicy()
    self.dex_pool_dict = {}
    self.string_index_section_offset = NO_OFFSET
    self.type_section_offset = NO_OFFSET
    self.proto_section_offset = NO_OFFSET
    self.field_section_offset = NO_OFFSET
    self.method_section_offset = NO_OFFSET
    self.class_index_section_offset = NO_OFFSET
    self.call_site_section_offset = NO_OFFSET
    self.method_handle_section_offset = NO_OFFSET

    self.string_data_section_offset = NO_OFFSET
    self.class_data_section_offset = NO_OFFSET
    self.type_list_section_offset = NO_OFFSET
    self.encoded_array_section_offset = NO_OFFSET
    self.annotation_section_offset = NO_OFFSET
    self.annotation_set_section_offset = NO_OFFSET
    self.annotation_set_ref_section_offset = NO_OFFSET
    self.annotation_directory_section_offset = NO_OFFSET
    self.debug_section_offset = NO_OFFSET
    self.code_section_offset = NO_OFFSET
    self.map_section_offset = NO_OFFSET

    self.num_annotation_set_ref_items = 0
    self.num_annotation_directory_items = 0
    self.num_debug_info_items = 0
    self.num_code_item_items = 0
    self.num_class_data_items = 0

    self.param_annotation_offset_map = {}

  def write(self, stream):
    for clazz in self.dex_class_pool.classes:
      clazz.fix()
      index = self.multidex_policy.get_multidex_index(clazz)
      index = 1
      if index not in self.dex_pool_dict:
        self.dex_pool_dict[index] = []
      self.dex_pool_dict[index].append(clazz)

    for dex_pool_index in self.dex_pool_dict:
      stream.set_output_index(index)
      self.build_dex(self.dex_pool_dict[dex_pool_index], stream)
      #stream.save()

  def build_dex(self, dex_pool, stream):
    manager = self.manager
    
    manager.build_string_section(dex_pool)
    manager.build_type_section(dex_pool)
    manager.build_proto_section(dex_pool)
    manager.build_field_section(dex_pool)
    manager.build_method_section(dex_pool)
    manager.build_class_def_section(dex_pool)
    manager.build_call_site_id_section(dex_pool) # pass, for reflection
    manager.build_method_handle_section(dex_pool) # pass, for reflection
    manager.build_map_list_section(dex_pool)
    manager.build_type_list_section(dex_pool)
    #manager.build_annotation_section(dex_pool)
    #manager.build_annotation_set_section(dex_pool)
    manager.build_hiddenapi_class_data_item_section(dex_pool)
    for x in manager.section_map:
      manager.section_map[x].freeze()

    data_section_offset = manager.get_data_section_offset()
    buf = bytearray()
    header_writer = OutputStream(buf, 0)
    index_writer = OutputStream(buf, SIZE_HEADER_ITEM)
    print('data section offset : ' + str(data_section_offset))
    offset_writer = OutputStream(buf, data_section_offset)
    
    self.write_strings(index_writer, offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_types(index_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_type_lists(offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_protos(index_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_fields(index_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_methods(index_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)

    method_handle_writer = OutputStream(buf, index_writer.get_position() + 
      manager.get_section(SECTION_CLASS).get_item_count() * CLASS_DEF_ITEM_SIZE +
      manager.get_section(SECTION_CALL_SITE).get_item_count() * CALL_SITE_ID_ITEM_SIZE
    )

    self.write_method_handles(method_handle_writer)
    method_handle_writer.close()

    self.write_encoded_arrays(offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)

    call_site_writer = OutputStream(buf, index_writer.get_position() + 
      manager.get_section(SECTION_CLASS).get_item_count() * CLASS_DEF_ITEM_SIZE)
    self.write_call_sites(call_site_writer)
    call_site_writer.close()

    self.write_annotations(offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_annotation_sets(offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_annotation_set_refs(offset_writer, dex_pool)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_annotation_directories(offset_writer, dex_pool)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_debug_and_code_items(offset_writer, TempOutputStream(bytearray()))
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_classes(index_writer, offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_map_item(offset_writer)
    offset_writer.align()
    assert(offset_writer.position % 4 == 0)
    self.write_header(header_writer, data_section_offset, len(buf))
    #header_writer.close()
    #index_writer.close()
    #offset_writer.close()

    self.update_signature(buf)
    self.update_check_sum(buf)



  def get_section(self, key):
    return self.manager.get_section(key)

  def write_strings(self, index_writer, offset_writer):
    self.string_index_section_offset = index_writer.get_position()
    self.string_data_section_offset = offset_writer.get_position()
    size = 0
    for item in self.get_section(SECTION_STRING).get_items():
      size += 1
      item_off = offset_writer.get_position()
      index_writer.write_uint(item_off)
      string_val = item

      offset_writer.write_uleb(len(string_val))
      offset_writer.write_string(string_val)
      offset_writer.write_ubyte(0)
    

  def write_types(self, index_writer):
    self.type_section_offset = index_writer.get_position()
    for item in self.get_section(SECTION_TYPE).get_items():
      try:
        index_writer.write_uint(self.get_section(SECTION_STRING).get_item_index(
        item
        ))
      except:
        pass

  def write_debug_and_code_items(self, offset_writer, deferred_stream):
    ehbuf = TempOutputStream(bytearray())
    self.debug_section_offset = offset_writer.get_position()
    # pass write debug section!
    code_writer = TempOutputStream(bytearray())

    offset_writer.align()
    self.code_section_offset = offset_writer.get_position()

    for clazz in self.get_section(SECTION_CLASS).get_items():
      direct_methods = clazz.get_direct_methods()
      virtual_methods = clazz.get_virtual_methods()
      for method in direct_methods + virtual_methods:
        try_blocks = method.get_try_blocks()
        instructions = method.get_instructions()
        #debug_items = method.get_debug_items()
        #debug_item_offset = write_debug_item(offset_writer, debug_writer,
        #method, debug_items
        #)
        debug_item_offset = 0
        code_item_offset = self.write_code_item(code_writer, ehbuf, method, try_blocks, instructions, debug_item_offset)
        if code_item_offset != -1:
          method.code_item_offset = code_item_offset + self.code_section_offset
          #print('code item offset is 0x{:08x}'.format(code_item_offset + self.code_section_offset))
        else:
          method.code_item_offset = 0
          #code_offsets.append(CodeItemOffset(method, code_item_offset))
    offset_writer.align()
    code_writer.write_to(offset_writer)

  def write_code_item(self, code_writer, ehbuf, method, try_blocks, instructions, debug_item_offset):
    if instructions is None and debug_item_offset == 0: return -1
    if len(instructions) == 0 and debug_item_offset == 0: return -1
    logging = False
    if 'com/google/ads/util/b' in method.clazz.type:
      logging = True

    #print('write code item for method {} {}'.format(method.clazz.type, method.name))
    self.num_code_item_items += 1
    code_writer.align()
    code_item_offset = code_writer.get_position()
    is_static = method.is_static()
    method.register_count = max(method.register_count, get_parameter_register_count(method.proto.parameters, is_static))
    if instructions is None:
      code_writer.write_ushort(method.register_count) # register
      code_writer.write_ushort(
      get_parameter_register_count(method.proto.parameters, is_static)
      ) # ins

      code_writer.write_ushort(0) # outs
      code_writer.write_ushort(0) # tries
      code_writer.write_uint(debug_item_offset) # debug_info_off
      code_writer.write_uint(0) # insns_size
      return code_item_offset
    #try_blocks = TryListBuilder.massage_try_blocks(try_blocks)
    out_param_count = 0
    code_unit_count = 0
    param_count = 0
    for ins in instructions:
      code_unit_count += ins.get_code_unit_count() #.get_code_unit_count()

      if ins.ref_type == INSTRUCT_TYPE_METHOD:
        method_ref = ins.ref
        opcode = ins.get_op()
        if InstructionUtil.is_invoke_polymorphic(opcode):
          if logging:
            print("instruction was(polymorphic) {}".format(opcode))
            print("register count from ins is {}".format(ins.get_register_count()))
          param_count = ins.get_register_count()
        else:
          if logging:
            print("instruction was {}".format(opcode))
            #paramCount = MethodUtil.getParameterRegisterCount(methodRef, InstructionUtil.isInvokeStatic(opcode));
          param_count = get_parameter_register_count(method_ref.parameters, InstructionUtil.is_invoke_static(opcode))
          if logging:
            print("register count from ins.ref is {}".format(param_count))

          #param_count = self.get_param_register_count(method_ref, InstructionUtil.is_invoke_static(opcode))

        if param_count > out_param_count:
          if logging:            
            print("out_param_count update to {} -> {}".format(out_param_count, param_count))
            print("method.register_count is {}".format(method.register_count))
          out_param_count = param_count
    if out_param_count > 5:
      method.register_count = max(out_param_count, method.register_count)
    code_writer.write_ushort(method.register_count) # register
    code_writer.write_ushort(
      get_parameter_register_count(method.proto.parameters, is_static)
    ) # ins

    code_writer.write_ushort(out_param_count)
    code_writer.write_ushort(len(try_blocks))
    code_writer.write_uint(debug_item_offset)

    ins_writer = InstructionWriter(code_writer, self)

    code_writer.write_uint(code_unit_count)
    code_offset = 0

    for ins in instructions:
      ins_writer.write(ins)
      code_offset += len(ins)#.en(get_code_units()

    if len(try_blocks) > 0:
      code_writer.align() # padding
      #if code_unit_count % 2 == 1: code_writer.write_ushort(0x0000)

      handler_map = dict()
      for try_block in try_blocks:
        key = str(try_block)
        handler_map[key] = 0
      ehbuf.write_uleb(len(handler_map))

      for try_block in try_blocks:
        if try_block.get_start_addr() > code_unit_count:
          raise Exception('start addr is large then code_unit_count({} > {})'.format(try_block.get_start_addr(), code_unit_count))
        code_writer.write_uint(try_block.get_start_addr())
        code_writer.write_ushort(try_block.get_code_count())

        if len(try_block.get_exception_handlers()) == 0:
          raise Exception("try block has no exception handlers")


        key = str(try_block)
        offset = handler_map[key]
        if offset != 0:
          code_writer.write_ushort(offset)
          continue
          #raise Exception('offset != 0')
        offset = ehbuf.get_position()
        code_writer.write_ushort(offset)
        handler_map[key] = offset

        eh_size = len(try_block.get_exception_handlers())
        eh_last = try_block.get_exception_handlers()[-1]
        if eh_last.get_exception_type() is None:
          eh_size = -eh_size + 1
      
        ehbuf.write_sleb(eh_size)
        for eh in try_block.get_exception_handlers():
          exception_type = eh.get_exception_type() ## need define handler_class, now, handler is tuple, there is no function
          code_addr = eh.get_handler_addr() 
          if exception_type is not None:
              # regular
            ehbuf.write_uleb(self.get_section(SECTION_TYPE).get_item_index(exception_type))
            ehbuf.write_uleb(code_addr)
          else:
            #catch(Throwable)
            ehbuf.write_uleb(code_addr)

    if ehbuf.get_position() > 0:
      ehbuf.write_to(code_writer)
    return code_item_offset

  def calc_map_list_item_count(self):
    num_items = 2 # header, map_list_item

    if self.get_section(SECTION_STRING).size(): num_items += 1 # for data

    num_items += len(list(filter(lambda x : x > 0, [self.get_section(x).size() for x in [SECTION_STRING, SECTION_TYPE, SECTION_PROTO, SECTION_FIELD, SECTION_METHOD, SECTION_CALL_SITE,
    SECTION_METHOD_HANDLE, SECTION_TYPE_LIST, SECTION_ENCODED_ARRAY, SECTION_ANNOTATION, SECTION_CLASS]])))

    if self.get_section(SECTION_ANNOTATION_SET).size() > 0 or self.should_create_empty_annotation_set():
      num_items += 1
    if self.num_annotation_set_ref_items > 0:
      num_items += 1
    if self.num_annotation_directory_items > 0:
      num_items += 1
    if self.num_debug_info_items > 0:
      num_items += 1
    if self.num_code_item_items > 0:
      num_items += 1
    if self.num_class_data_items > 0:
      num_items += 1
    #return 2
    return num_items


  def write_map_item(self, offset_writer):
    offset_writer.align()
    self.map_section_offset = offset_writer.get_position()
    num_items = self.calc_map_list_item_count()
    offset_writer.write_uint(num_items)

    self.write_map_item_object(offset_writer, HEADER_ITEM, 1, 0)
    
    self.write_map_item_object(offset_writer, STRING_ID_ITEM, self.get_section(SECTION_STRING).size(), self.string_index_section_offset)
    self.write_map_item_object(offset_writer, TYPE_ID_ITEM, self.get_section(SECTION_TYPE).size(), self.type_section_offset)
    self.write_map_item_object(offset_writer, PROTO_ID_ITEM, self.get_section(SECTION_PROTO).size(), self.proto_section_offset)
    self.write_map_item_object(offset_writer, FIELD_ID_ITEM, self.get_section(SECTION_FIELD).size(), self.field_section_offset)
    self.write_map_item_object(offset_writer, METHOD_ID_ITEM, self.get_section(SECTION_METHOD).size(), self.method_section_offset)
    self.write_map_item_object(offset_writer, CLASS_DEF_ITEM, self.get_section(SECTION_CLASS).size(), self.class_index_section_offset)
    self.write_map_item_object(offset_writer, CALL_SITE_ID_ITEM, self.get_section(SECTION_CALL_SITE).size(), self.call_site_section_offset)
    self.write_map_item_object(offset_writer, METHOD_HANDLE_ITEM, self.get_section(SECTION_METHOD_HANDLE).size(), self.method_handle_section_offset)

    # data section
    self.write_map_item_object(offset_writer, STRING_DATA_ITEM, self.get_section(SECTION_STRING).size(), self.string_data_section_offset)
    self.write_map_item_object(offset_writer, TYPE_LIST, self.get_section(SECTION_TYPE_LIST).size(), self.type_list_section_offset)
    self.write_map_item_object(offset_writer, ENCODED_ARRAY_ITEM, self.get_section(SECTION_ENCODED_ARRAY).size(), self.encoded_array_section_offset)
    self.write_map_item_object(offset_writer, ANNOTATION_ITEM, self.get_section(SECTION_ANNOTATION).size(), self.annotation_section_offset)
    self.write_map_item_object(offset_writer, ANNOTATION_SET_ITEM, self.get_section(SECTION_ANNOTATION_SET).size() + 1 if self.should_create_empty_annotation_set() else 0, self.annotation_set_section_offset)
    self.write_map_item_object(offset_writer, ANNOTATION_SET_REF_LIST, self.num_annotation_set_ref_items, self.annotation_set_ref_section_offset)
    self.write_map_item_object(offset_writer, ANNOTATION_DIRECTORY_ITEM, self.num_annotation_directory_items, self.annotation_directory_section_offset)
    self.write_map_item_object(offset_writer, DEBUG_INFO_ITEM, self.num_debug_info_items, self.debug_section_offset)
    self.write_map_item_object(offset_writer, CODE_ITEM, self.num_code_item_items, self.code_section_offset)
    self.write_map_item_object(offset_writer, CLASS_DATA_ITEM, self.num_class_data_items, self.class_data_section_offset)
    
    self.write_map_item_object(offset_writer, MAP_LIST, 1, self.map_section_offset)

  def write_map_item_object(self, offset_writer, item_type, size, offset):
    if size > 0:
      offset_writer.write_ushort(item_type)
      offset_writer.write_ushort(0)
      offset_writer.write_uint(size)
      offset_writer.write_uint(offset)
    
  
  def write_type_lists(self, writer):
    writer.align()
    self.type_list_section_offset = writer.position
    type_list_section = self.get_section(SECTION_TYPE_LIST)

    for item in type_list_section.get_items():
      prev_offset = writer.position
      align_offset = writer.align()
      #print("offset aligned for {} -> {}({})".format(prev_offset, writer.position, align_offset))
      type_list_section.set_offset_by_item(item, writer.position)
      types = item.get_types()
      writer.write_uint(len(types))
      for t in types:
        #print('write typeindex {} -> {}'.format(t, self.get_section(SECTION_TYPE).get_item_index(t)))
        writer.write_ushort(self.get_section(SECTION_TYPE).get_item_index(t))


  def write_protos(self, writer):
    self.proto_section_offset = writer.position
    index = 0
    for item in self.get_section(SECTION_PROTO).get_items():
      index += 1
      writer.write_uint(
        self.get_section(SECTION_STRING).get_item_index(
          item.shorty
        )
      )
      writer.write_uint(
        self.get_section(SECTION_TYPE).get_item_index(
          item.return_type
        )
      )
      param_off = self.get_section(SECTION_TYPE_LIST).get_offset_by_item(
          item.parameters
        )
      writer.write_uint(
        self.get_section(SECTION_TYPE_LIST).get_offset_by_item(
          item.parameters
        )
      )

  def write_fields(self, writer):
    self.field_section_offset = writer.position
    index = 0
    type_section = self.get_section(SECTION_TYPE)
    string_section = self.get_section(SECTION_STRING)
    for x in self.get_section(SECTION_FIELD).get_items():
      x.index = index
      index += 1
      try:
        clazz_type = x.clazz.type
      except:
        clazz_type = x.clazz

      writer.write_ushort(type_section.get_item_index(clazz_type))
      writer.write_ushort(type_section.get_item_index(x.type))
      writer.write_uint(string_section.get_item_index(x.name))

  def write_methods(self, writer):
    self.method_section_offset = writer.position
    index = 0
    type_section = self.get_section(SECTION_TYPE)
    string_section = self.get_section(SECTION_STRING)
    proto_section = self.get_section(SECTION_PROTO)
    method_section = self.get_section(SECTION_METHOD)

    for x in method_section.get_items():
      x.index = index
      index += 1
      writer.write_ushort(type_section.get_item_index(x.clazz.type))
      writer.write_ushort(proto_section.get_item_index(x.proto))
      writer.write_uint(string_section.get_item_index(x.name))

    
  def write_classes(self, index_writer, offset_writer):
    self.class_index_section_offset = index_writer.position
    self.class_data_section_offset = offset_writer.position

    class_section = self.get_section(SECTION_CLASS)
    index = 0
    for x in class_section.get_items():
      index = self.write_class(index_writer, offset_writer, index, x)

  def write_class(self, index_writer, offset_writer, index, clazz):
    if clazz is None: return index # not in dex
    if clazz.index != NO_INDEX: return index # writed

    clazz.index = 0

    index = self.write_class(index_writer, offset_writer, index, clazz.superclass)
    for x in clazz.interfaces:
      index = self.write_class(index_writer, offset_writer, index, x)
    clazz.index = index
    index += 1
    type_section = self.get_section(SECTION_TYPE)
    type_list_section = self.get_section(SECTION_TYPE_LIST)
    string_section = self.get_section(SECTION_STRING)
    
    index_writer.write_uint(type_section.get_item_index(clazz.type))
    index_writer.write_uint(clazz.access_flags)
    index_writer.write_uint(type_section.get_item_index(clazz.superclass))
    index_writer.write_uint(type_list_section.get_offset_by_item(clazz.interfaces))
    index_writer.write_uint(string_section.get_item_index(clazz.source_file_name)) # source_file_idx
    index_writer.write_uint(clazz.annotation_dir_offset)
   

    static_fields = clazz.get_sorted_static_fields(self.get_section(SECTION_FIELD))
    instance_fields = clazz.get_sorted_instance_fields(self.get_section(SECTION_FIELD))
    direct_methods = clazz.get_sorted_direct_methods(self.get_section(SECTION_METHOD))
    virtual_methods = clazz.get_sorted_virtual_methods(self.get_section(SECTION_METHOD))

    offset = offset_writer.position
    clazz_has_data = len(static_fields) > 0 or len(instance_fields) > 0 or len(direct_methods) > 0 or len(virtual_methods) > 0
    if not clazz_has_data:
      offset = NO_OFFSET
    index_writer.write_uint(offset)
    encoded_array_section = self.get_section(SECTION_ENCODED_ARRAY)
    if clazz.static_initializers:
      offset = encoded_array_section.get_offset_by_item(clazz.static_initializers)
    else:
      offset = NO_OFFSET
    index_writer.write_uint(offset)
    

    if not clazz_has_data: return index

    self.num_class_data_items += 1

    offset_writer.write_uleb(len(static_fields))
    offset_writer.write_uleb(len(instance_fields))
    offset_writer.write_uleb(len(direct_methods))
    offset_writer.write_uleb(len(virtual_methods))

    self.write_encoded_fields(offset_writer, static_fields)
    self.write_encoded_fields(offset_writer, instance_fields)
    self.write_encoded_methods(offset_writer, direct_methods)
    self.write_encoded_methods(offset_writer, virtual_methods)

    return index

  def write_encoded_fields(self, offset_writer, field_list):
    prev_index = 0
    field_section = self.get_section(SECTION_FIELD)
    
    for field in field_list:
      index = field_section.get_item_index(field)
      #print("index : {} prev_index : {}".format(index, prev_index))
      offset_writer.write_uleb(index - prev_index)
      offset_writer.write_uleb(field.access_flags)
      prev_index = index
  
  def write_encoded_methods(self, offset_writer, method_list):
    prev_index = 0
    method_section = self.get_section(SECTION_METHOD)
    for method in method_list:
      index = method_section.get_item_index(method)
      #print("index : {} prev_index : {}".format(index, prev_index))
      offset_writer.write_uleb(index - prev_index)
      offset_writer.write_uleb(method.access_flags)
      offset_writer.write_uleb(method.code_item_offset)
      prev_index = index

  def write_call_sites(self, writer):
    pass # skip

  def write_method_handles(self, writer):
    pass # skip

  def write_encoded_arrays(self, writer):
    self.encoded_array_section_offset = writer.position

    encoded_array_section = self.get_section(SECTION_ENCODED_ARRAY)

    for arr in encoded_array_section.get_items():
      encoded_array_section.set_offset_by_item(arr, writer.position)
      encoded_array = arr
      writer.write_uleb(len(arr))
      for val in encoded_array:
        self.write_encoded_value(writer, val)

  

  def write_annotations(self, writer):
    self.annotation_section_offset = writer.position
    annotation_section = self.get_section(SECTION_ANNOTATION)
    type_section = self.get_section(SECTION_TYPE)
    string_section = self.get_section(SECTION_STRING)
    
    for ann in annotation_section.get_items():
      ann.offset = writer.position
      writer.write_ubyte(ann.visibility)
      writer.write_uleb(type_section.get_item_index(ann.type))
      elems = ann.elements
      writer.write_uleb(len(elems))
      for elem in elems:
        name_idx = string_section.get_item_index(elem[0])
        # if isinstance(elem[1], list):
        #   print(' {} - {}'.format(elem[0], [str(x) for x in elem[1]]))

        # else:
        #   print(' {} - {}'.format(elem[0], elem[1]))

        writer.write_uleb(name_idx)
        self.write_encoded_value(writer, elem[1])


  def write_annotation_sets(self, writer):
    writer.align()
    self.annotation_set_section_offset = writer.position
    if self.should_create_empty_annotation_set(): writer.write_uint(0)

    annotation_set_section = self.get_section(SECTION_ANNOTATION_SET)
    for index in annotation_set_section.get_items():
      annotations = annotation_set_section.get_item_by_index(index)
      if annotations is None:
        print('[warning] annotation index {} is None'.format(index))
        continue

      #print('process annotation : {}'.format([str(x) for x in annotations]))

      writer.align()
      annotation_set_section.set_offset_by_index(index, writer.position)
      writer.write_uint(len(annotations))
      for annotation in annotations:
        writer.write_uint(annotation.offset)

  def hash_param_annotation(self, param_annotation):
    if isinstance(param_annotation, list):
      return '|'.join([str(self.hash_param_annotation(x)) for x in param_annotation])
    
    return hash(param_annotation)
  
  def write_annotation_set_refs(self, writer, dex_pool):
    writer.align()
    self.annotation_set_ref_section_offset = writer.position
    interned = {}
    ann_section = self.get_section(SECTION_ANNOTATION_SET)

    for clazz in dex_pool:
      for method in clazz.methods:
        param_annotation = method.param_annotations
        if not param_annotation: continue
        
        interned_key = self.hash_param_annotation(param_annotation)
        prev = interned.get(interned_key, -1)
        if prev != -1:
          method.annotation_set_ref_list_offset = prev
          self.param_annotation_offset_map[self.hash_param_annotation(param_annotation)] = prev
          #ann_section.set_offset_by_item(param_annotation, prev)
          continue

        writer.align()
        position = writer.position
        interned[interned_key] = position
        self.param_annotation_offset_map[self.hash_param_annotation(param_annotation)] = position
        #ann_section.set_offset_by_item(param_annotation, position)
        self.num_annotation_set_ref_items += 1
        writer.write_uint(len(param_annotation))

        for ann in param_annotation:
          
          offset = self.param_annotation_offset_map.get(self.hash_param_annotation(ann), NO_OFFSET)
          if offset != NO_OFFSET:
            writer.write_uint(offset)
          elif self.should_create_empty_annotation_set():
            writer.write_uint(self.annotation_set_section_offset)
          else:
            writer.write_uint(NO_OFFSET)


          
    

  def write_annotation_directories(self, writer, dex_buf):
    writer.align()
    self.annotation_directory_section_offset = writer.position
    interned = {}
    tmp_buf = bytearray() # little endian
    field_section = self.get_section(SECTION_FIELD)
    method_section = self.get_section(SECTION_METHOD)
    annotation_set_section = self.get_section(SECTION_ANNOTATION_SET)

    for clazz in dex_buf:
      #max_size = len(clazz.fields) * 8 + len(clazz.methods) * 16
      tmp_buffer = TempOutputStream(bytearray())
      field_annotations = 0
      method_annotations = 0
      param_annotations = 0
      fields = clazz.get_sorted_fields(field_section)
      methods = clazz.get_sorted_methods(method_section)
      for field in fields:
        if field.annotations:
          field_annotations += 1
          tmp_buffer.write_uint(field_section.get_item_index(field))
          tmp_buffer.write_uint(annotation_set_section.get_offset_by_item(field.annotations))
          
      for method in methods:
        if method.annotations:
          method_annotations += 1
          tmp_buffer.write_uint(method_section.get_item_index(method))
          try:
            offset = annotation_set_section.get_offset_by_item(method.annotations)
          except:
            print('[WARNING] {} - {} annotation not found'.format(clazz.type, method.name))
            offset = 0

          tmp_buffer.write_uint(offset)
      
      for method in clazz.methods:
        if method.annotation_set_ref_list_offset != NO_OFFSET:
          param_annotations += 1
          tmp_buffer.write_uint(method_section.get_item_index(method))
          tmp_buffer.write_uint(method.annotation_set_ref_list_offset)
      
      if field_annotations == 0 and method_annotations == 0 and param_annotations == 0:
        if clazz.annotations:
          key = ""
          for ann in clazz.annotations:
            key += str(ann)
          dir_offset = interned.get(key, None)
          if dir_offset:
            clazz.annotation_dir_offset = dir_offset
            continue
          else:
            interned[key] = writer.position
        else:
          continue
      self.num_annotation_directory_items += 1
      clazz.annotation_dir_offset = writer.position
      if clazz.annotations:
        writer.write_uint(annotation_set_section.get_offset_by_item(clazz.annotations))
      else:
        writer.write_uint(0) 
      writer.write_uint(field_annotations)
      writer.write_uint(method_annotations)
      writer.write_uint(param_annotations)
      tmp_buffer.write_to(writer)

  def write_encoded_value(self, writer, val):
    #if isinstance(val, list):
    #  for x in val:
    #    self.write_encoded_value(writer, x)
    #  return
    if not isinstance(val, DexValue):
      val = DexValue(val)
    if isinstance(val, list):
      for x in val:
        self.write_encoded_value(writer, x)
      return
    val.encode(self.manager, writer)

  def get_magic(self, api_level):
    dex_version = 0x35
    return bytearray([0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, dex_version, 0x00])
  def write_header(self, writer, data_offset, file_size):
    print("file size is {}".format(file_size))
    writer.write_byte_array(self.get_magic("opcodes.api"))

    writer.write_uint(0) # checksum
    writer.write_arrays(bytearray(20))

    writer.write_uint(file_size)
    writer.write_uint(SIZE_HEADER_ITEM)
    writer.write_uint(LITTLE_ENDIAN_TAG)

    writer.write_uint(0) # link
    writer.write_uint(0) # link

    writer.write_uint(self.map_section_offset)


    self.write_section_info(writer, self.get_section(SECTION_STRING).size(), self.string_index_section_offset)
    self.write_section_info(writer, self.get_section(SECTION_TYPE).size(), self.type_section_offset)
    self.write_section_info(writer, self.get_section(SECTION_PROTO).size(), self.proto_section_offset)
    self.write_section_info(writer, self.get_section(SECTION_FIELD).size(), self.field_section_offset)
    self.write_section_info(writer, self.get_section(SECTION_METHOD).size(), self.method_section_offset)
    self.write_section_info(writer, self.get_section(SECTION_CLASS).size(), self.class_index_section_offset)

    writer.write_uint(file_size - data_offset)
    writer.write_uint(data_offset)

  def write_section_info(self, writer, num_items, offset):
    writer.write_uint(num_items)
    if num_items <= 0:
      offset = 0
    writer.write_uint(offset)

  def update_check_sum(self, buf):
    from dexassist.writer.dex import stream
    checksum = zlib.adler32(buf[12:]) & 0xffffffff
    
    buf[8:12] = struct.pack(stream.UINT_FMT, checksum)

    

  def update_signature(self, buf):
    from dexassist.writer.dex import stream
    sha = hashlib.sha1()
    #buf[file_size_offset:file_size_offset + 4] = struct.pack(stream.UINT_FMT, len(buf))
    sha.update(buf[32:])
    sig = sha.digest()

    buf[12:32] = sig
    
    

  def should_create_empty_annotation_set(self):
    return True # we don't make dex, just rebuild dex so assert dex is always valid.
    # if opcodes.api < 17, app will be crash before android 4.2
  
  def verify_dex(self, buf):
    pass

  def check_intra_section(self, map_list):
    offset = 0
    count = len(map_list)
    for item in map_list:
      pass

    while count != 0:
      item = 0

      current_offset = offset
      section_offset = 0


      count -= 1
