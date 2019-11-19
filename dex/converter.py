from dexassist import normalize
from dexassist.dex import dex
from dexassist.bytecodes import editor
from dexassist.bytecodes import base

class DexConverter(object):
  def get_dex(self, header, manager):
    dex = normalize.Dex()
    for x in manager.class_def_list:
      dex.add_class(self.create_dex_class(x, manager))
    return dex
  def translate_encoded_value(self, manager, encoded_value):
    if encoded_value.type == dex.ENCODED_VALUE_ARRAY:
      pass
    if encoded_value.type == dex.ENCODED_VALUE_STRING:
      pass
    if encoded_value.type == dex.ENCODED_VALUE_METHOD:
      pass

    return translate_encoded_value(encoded_value)

  def extract_from_annotation_set_item(self, parent, manager, annotation_set_item):
    ret = []
    for entry in annotation_set_item.entries:
      annotation_item = entry.annotation
      visibility = annotation_item.visibility
      type_idx = annotation_item.annotation.type_idx
      elements = []
      type_name = manager.string_list[type_idx]
      for x in range(annotation_item.annotation.size):
        name_idx = annotation_item.annotation.elements[x].name_idx
        value = annotation_item.annotation.elements[x].value

        elements.append((manager.string_list[name_idx],
            self.translate_encoded_value(manager, value)
        ))
      ret.append(
        normalize.DexAnnotation(parent, visibility, type_name, elements)
      )
    return ret

  #cdi : class_def_item
  def create_dex_class(self, cdi, manager):
    item = normalize.DexClassItem()
    item.type = manager.type_list[cdi.class_idx]
    item.access_flags = cdi.access_flags
    item.superclass = manager.type_list[cdi.superclass_idx]
    item.interfaces = [manager.type_list[x] for x in cdi.interfaces]
    item.name = item.type

    if cdi.source_file_idx:
      try:
        item.source_file_name = manager.string_list[cdi.source_file_idx]
      except:
        import traceback
        print("source file idx {} is not in string_list".format(cdi.source_file_idx))

    if cdi.static_values:
      item.static_values = [x.value for x in cdi.static_values.value.values]
    field_annotation_table = {}
    method_annotation_table = {}
    param_annotation_table = {}
    if cdi.annotations:
      a = cdi.annotations
      if a.class_item:
        annotations = self.extract_from_annotation_set_item(item, manager, a.class_item)
        item.annotations = annotations
      for field_annotation in a.field_annotations:
        field_annotation_table[field_annotation.field_idx] = self.extract_from_annotation_set_item(manager.field_list[field_annotation.field_idx], manager, field_annotation.annotation)
      for method_annotation in a.method_annotations:
        method_annotation_table[method_annotation.method_idx] = self.extract_from_annotation_set_item(manager.method_list[method_annotation.method_idx], manager, method_annotation.annotation)
      for param_annotation in a.parameter_annotations:
        param_annotation_table[param_annotation.method_idx] = []
        for refitem in param_annotation.annotation_ref.list:
          annotation = refitem.annotation
          if annotation:
            annotation = self.extract_from_annotation_set_item(manager.method_list[param_annotation.method_idx], manager, annotation)
          param_annotation_table[param_annotation.method_idx].append(annotation)


    field_idx = 0
    if cdi.data is None:
      return item

    for f in cdi.data.static_fields:
      field_idx += f.field_idx_diff
      access_flags = f.access_flags
      field = manager.field_list[field_idx]
      field_name = manager.string_list[field.name_idx]
      type_name = manager.type_list[field.type_idx]

      f = self.create_dex_field(item, field_name, type_name, access_flags)
      f.annotations = field_annotation_table.get(field_idx, [])
      item.fields.append(f)
    field_idx = 0
    for f in cdi.data.instance_fields:
      field_idx += f.field_idx_diff
      access_flags = f.access_flags
      field = manager.field_list[field_idx]
      field_name = manager.string_list[field.name_idx]
      type_name = manager.type_list[field.type_idx]
      f = self.create_dex_field(item, field_name, type_name, access_flags)
      f.annotations = field_annotation_table.get(field_idx, [])
      item.fields.append(f)

    method_idx = 0
    for m in cdi.data.direct_methods:
      method_idx += m.method_idx_diff
      method_item = manager.method_list[method_idx]
      class_idx = method_item.class_idx
      proto_idx = method_item.proto_idx
      name_idx = method_item.name_idx

      method_name = manager.string_list[name_idx]
      access_flags = m.access_flags
      code = m.code
      proto = manager.proto_list[proto_idx]
      return_type_idx = proto.return_type_idx
      parameter = []
      if proto.type_list:
        for type_item in proto.type_list.list:
          parameter_type_idx = type_item.type_idx
          type_info = manager.type_list[parameter_type_idx]
          parameter.append(type_info)
      method_signature = '{}({})'.format(manager.type_list[return_type_idx] , ''.join(parameter))

      x = self.create_dex_method(manager, item, method_name, access_flags, method_signature, code)
      x.annotations = method_annotation_table.get(method_idx, [])
      x.param_annotations = param_annotation_table.get(method_idx, [])
      item.methods.append(x)
    
    method_idx = 0
    for m in cdi.data.virtual_methods:
      method_idx += m.method_idx_diff
      method_item = manager.method_list[method_idx]
      class_idx = method_item.class_idx
      proto_idx = method_item.proto_idx
      name_idx = method_item.name_idx

      method_name = manager.string_list[name_idx]
      access_flags = m.access_flags
      code = m.code
      
      proto = manager.proto_list[proto_idx]
      return_type_idx = proto.return_type_idx
      parameter = []
      if proto.type_list:
        for type_item in proto.type_list.list:
          parameter_type_idx = type_item.type_idx
          type_info = manager.type_list[parameter_type_idx]
          parameter.append(type_info)
      
      method_signature = '{}({})'.format(manager.type_list[return_type_idx] , ''.join(parameter))
      x = self.create_dex_method(manager, item, method_name, access_flags, method_signature, code)
      x.annotations = method_annotation_table.get(method_idx, [])
      x.param_annotations = param_annotation_table.get(method_idx, [])
      item.methods.append(x)


    return item


  #ef : encodedfield
  def create_dex_field(self, parent, field_name, type_name, access_flags):
    f = normalize.DexField(parent, field_name, type_name, access_flags)
    return f

  def create_dex_method(self, manager, parent, method_name, access_flags, signature, code):
    if code:
      x = code_to_editor(manager, code)
    m = normalize.DexMethod(parent, method_name, access_flags, signature, x)
    return m


def translate_encoded_value(encoded_value):
  #print('translate value(type : {}) : {} -> {}'.format(encoded_value.type, encoded_value, encoded_value.value))
  
  return encoded_value.value

def translate_encoded_array(encoded_array):
  #print(encoded_array)
  return [x.value for x in encoded_array.values]

def code_to_editor(manager, code):
  e = editor.Editor()
  e.manager = manager
  ir = CodeItemReader(e, manager, code)
  return e


class ByteCodeConverter(object):
  def __init__(self, manager):
    pass



class DexWriter(object):
  def __init__(self, dex):
    self.dex = dex
  def save_as(self, stream):
    pass



class CodeStream(object):
  def __init__(self, insns_array):
    self.buf = insns_array
    self.index = 0
  def peek(self):
    return self.buf[self.index]
  def read(self):
    ret = self.peek()
    self.index += 1
    return ret

class CodeItemReader(object):
  def __init__(self, editor, manager, code_item):
    self.tries = []
    self.opcodes = []
    self.editor = editor
    self.manager = manager
    stream = CodeStream(code_item.insns)

    while stream.index < code_item.insns_size:
      opcode = stream.peek() & 0xff
      instruction = base.OpcodeFactory.from_stream(opcode, self.editor.manager, stream)
      self.opcodes.append(instruction)
    type_addrs = []
    if code_item.tries and False:
      for t in code_item.tries:
        catch_handlers = t.handlers
        for handler in catch_handlers.list:
          for type_addr_pair in handler.handlers:
            type_idx, addr = type_addr_pair.type_idx, type_addr_pair.addr
            type_addrs.append((self.manager.type_list[type_idx], addr))
          catch_all_addr = handler.catch_all_addr


        trycatch = editor.TryCatch(self.editor, t.start_addr, t.start_addr + t.insn_count - 1, type_addrs, catch_all_addr)
        self.editor.tries.append(trycatch)
    self.editor.opcode_list = self.opcodes

