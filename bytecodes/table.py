import base
# for backup opcode
OPCODE_TABLE = {
    0x00: [base.Instruction10x, "nop"],
    0x01: [base.Instruction12x, "move"],
    0x02: [base.Instruction22x, "move/from16"],
    0x03: [base.Instruction32x, "move/16"],
    0x04: [base.Instruction12x, "move-wide"],
    0x05: [base.Instruction22x, "move-wide/from16"],
    0x06: [base.Instruction32x, "move-wide/16"],
    0x07: [base.Instruction12x, "move-object"],
    0x08: [base.Instruction22x, "move-object/from16"],
    0x09: [base.Instruction32x, "move-object/16"],
    0x0a: [base.Instruction11x, "move-result"],
    0x0b: [base.Instruction11x, "move-result-wide"],
    0x0c: [base.Instruction11x, "move-result-object"],
    0x0d: [base.Instruction11x, "move-exception"],
    0x0e: [base.Instruction10x, "return-void"],
    0x0f: [base.Instruction11x, "return"],
    0x10: [base.Instruction11x, "return-wide"],
    0x11: [base.Instruction11x, "return-object"],
    0x12: [base.Instruction11n, "const/4"],
    0x13: [base.Instruction21s, "const/16"],
    0x14: [base.Instruction31i, "const"],
    0x15: [base.Instruction21h, "const/high16"],
    0x16: [base.Instruction21s, "const-wide/16"],
    0x17: [base.Instruction31i, "const-wide/32"],
    0x18: [base.Instruction51l, "const-wide"],
    0x19: [base.Instruction21h, "const-wide/high16"],
    0x1a: [base.Instruction21c, "const-string", INSTRUCT_TYPE_STRING],
    0x1b: [base.Instruction31c, "const-string/jumbo", INSTRUCT_TYPE_STRING],
    0x1c: [base.Instruction21c, "const-class", INSTRUCT_TYPE_TYPE],
    0x1d: [base.Instruction11x, "monitor-enter"],
    0x1e: [base.Instruction11x, "monitor-exit"],
    0x1f: [base.Instruction21c, "check-cast", INSTRUCT_TYPE_TYPE],
    0x20: [base.Instruction22c, "instance-of", INSTRUCT_TYPE_TYPE],
    0x21: [base.Instruction12x, "array-length"],
    0x22: [base.Instruction21c, "new-instance", INSTRUCT_TYPE_TYPE],
    0x23: [base.Instruction22c, "new-array", INSTRUCT_TYPE_TYPE],
    0x24: [base.Instruction35c, "filled-new-array", INSTRUCT_TYPE_TYPE],
    0x25: [base.Instruction3rc, "filled-new-array/range", INSTRUCT_TYPE_TYPE],
    0x26: [base.Instruction31t, "fill-array-data"],
    0x27: [base.Instruction11x, "throw"],
    0x28: [base.Instruction10t, "goto"],
    0x29: [base.Instruction20t, "goto/16"],
    0x2a: [base.Instruction30t, "goto/32"],
    0x2b: [base.Instruction31t, "packed-switch"],
    0x2c: [base.Instruction31t, "sparse-switch"],
    0x2d: [base.Instruction23x, "cmpl-float"],
    0x2e: [base.Instruction23x, "cmpg-float"],
    0x2f: [base.Instruction23x, "cmpl-double"],
    0x30: [base.Instruction23x, "cmpg-double"],
    0x31: [base.Instruction23x, "cmp-long"],
    0x32: [base.Instruction22t, "if-eq"],
    0x33: [base.Instruction22t, "if-ne"],
    0x34: [base.Instruction22t, "if-lt"],
    0x35: [base.Instruction22t, "if-ge"],
    0x36: [base.Instruction22t, "if-gt"],
    0x37: [base.Instruction22t, "if-le"],
    0x38: [base.Instruction21t, "if-eqz"],
    0x39: [base.Instruction21t, "if-nez"],
    0x3a: [base.Instruction21t, "if-ltz"],
    0x3b: [base.Instruction21t, "if-gez"],
    0x3c: [base.Instruction21t, "if-gtz"],
    0x3d: [base.Instruction21t, "if-lez"],
    # unused
    0x3e: [base.Instruction10x, "nop"],
    0x3f: [base.Instruction10x, "nop"],
    0x40: [base.Instruction10x, "nop"],
    0x41: [base.Instruction10x, "nop"],
    0x42: [base.Instruction10x, "nop"],
    0x43: [base.Instruction10x, "nop"],
    0x44: [base.Instruction23x, "aget"],
    0x45: [base.Instruction23x, "aget-wide"],
    0x46: [base.Instruction23x, "aget-object"],
    0x47: [base.Instruction23x, "aget-boolean"],
    0x48: [base.Instruction23x, "aget-byte"],
    0x49: [base.Instruction23x, "aget-char"],
    0x4a: [base.Instruction23x, "aget-short"],
    0x4b: [base.Instruction23x, "aput"],
    0x4c: [base.Instruction23x, "aput-wide"],
    0x4d: [base.Instruction23x, "aput-object"],
    0x4e: [base.Instruction23x, "aput-boolean"],
    0x4f: [base.Instruction23x, "aput-byte"],
    0x50: [base.Instruction23x, "aput-char"],
    0x51: [base.Instruction23x, "aput-short"],
    0x52: [base.Instruction22c, "iget", INSTRUCT_TYPE_FIELD],
    0x53: [base.Instruction22c, "iget-wide", INSTRUCT_TYPE_FIELD],
    0x54: [base.Instruction22c, "iget-object", INSTRUCT_TYPE_FIELD],
    0x55: [base.Instruction22c, "iget-boolean", INSTRUCT_TYPE_FIELD],
    0x56: [base.Instruction22c, "iget-byte", INSTRUCT_TYPE_FIELD],
    0x57: [base.Instruction22c, "iget-char", INSTRUCT_TYPE_FIELD],
    0x58: [base.Instruction22c, "iget-short", INSTRUCT_TYPE_FIELD],
    0x59: [base.Instruction22c, "iput", INSTRUCT_TYPE_FIELD],
    0x5a: [base.Instruction22c, "iput-wide", INSTRUCT_TYPE_FIELD],
    0x5b: [base.Instruction22c, "iput-object", INSTRUCT_TYPE_FIELD],
    0x5c: [base.Instruction22c, "iput-boolean", INSTRUCT_TYPE_FIELD],
    0x5d: [base.Instruction22c, "iput-byte", INSTRUCT_TYPE_FIELD],
    0x5e: [base.Instruction22c, "iput-char", INSTRUCT_TYPE_FIELD],
    0x5f: [base.Instruction22c, "iput-short", INSTRUCT_TYPE_FIELD],
    0x60: [base.Instruction21c, "sget", INSTRUCT_TYPE_FIELD],
    0x61: [base.Instruction21c, "sget-wide", INSTRUCT_TYPE_FIELD],
    0x62: [base.Instruction21c, "sget-object", INSTRUCT_TYPE_FIELD],
    0x63: [base.Instruction21c, "sget-boolean", INSTRUCT_TYPE_FIELD],
    0x64: [base.Instruction21c, "sget-byte", INSTRUCT_TYPE_FIELD],
    0x65: [base.Instruction21c, "sget-char", INSTRUCT_TYPE_FIELD],
    0x66: [base.Instruction21c, "sget-short", INSTRUCT_TYPE_FIELD],
    0x67: [base.Instruction21c, "sput", INSTRUCT_TYPE_FIELD],
    0x68: [base.Instruction21c, "sput-wide", INSTRUCT_TYPE_FIELD],
    0x69: [base.Instruction21c, "sput-object", INSTRUCT_TYPE_FIELD],
    0x6a: [base.Instruction21c, "sput-boolean", INSTRUCT_TYPE_FIELD],
    0x6b: [base.Instruction21c, "sput-byte", INSTRUCT_TYPE_FIELD],
    0x6c: [base.Instruction21c, "sput-char", INSTRUCT_TYPE_FIELD],
    0x6d: [base.Instruction21c, "sput-short", INSTRUCT_TYPE_FIELD],
    0x6e: [base.Instruction35c, "invoke-virtual", INSTRUCT_TYPE_METHOD],
    0x6f: [base.Instruction35c, "invoke-super", INSTRUCT_TYPE_METHOD],
    0x70: [base.Instruction35c, "invoke-direct", INSTRUCT_TYPE_METHOD],
    0x71: [base.Instruction35c, "invoke-static", INSTRUCT_TYPE_METHOD],
    0x72: [base.Instruction35c, "invoke-interface", INSTRUCT_TYPE_METHOD],
    # unused
    0x73: [base.Instruction10x, "nop"],
    0x74: [base.Instruction3rc, "invoke-virtual/range", INSTRUCT_TYPE_METHOD],
    0x75: [base.Instruction3rc, "invoke-super/range", INSTRUCT_TYPE_METHOD],
    0x76: [base.Instruction3rc, "invoke-direct/range", INSTRUCT_TYPE_METHOD],
    0x77: [base.Instruction3rc, "invoke-static/range", INSTRUCT_TYPE_METHOD],
    0x78: [base.Instruction3rc, "invoke-interface/range", INSTRUCT_TYPE_METHOD],
    # unused
    0x79: [base.Instruction10x, "nop"],
    0x7a: [base.Instruction10x, "nop"],
    0x7b: [base.Instruction12x, "neg-int"],
    0x7c: [base.Instruction12x, "not-int"],
    0x7d: [base.Instruction12x, "neg-long"],
    0x7e: [base.Instruction12x, "not-long"],
    0x7f: [base.Instruction12x, "neg-float"],
    0x80: [base.Instruction12x, "neg-double"],
    0x81: [base.Instruction12x, "int-to-long"],
    0x82: [base.Instruction12x, "int-to-float"],
    0x83: [base.Instruction12x, "int-to-double"],
    0x84: [base.Instruction12x, "long-to-int"],
    0x85: [base.Instruction12x, "long-to-float"],
    0x86: [base.Instruction12x, "long-to-double"],
    0x87: [base.Instruction12x, "float-to-int"],
    0x88: [base.Instruction12x, "float-to-long"],
    0x89: [base.Instruction12x, "float-to-double"],
    0x8a: [base.Instruction12x, "double-to-int"],
    0x8b: [base.Instruction12x, "double-to-long"],
    0x8c: [base.Instruction12x, "double-to-float"],
    0x8d: [base.Instruction12x, "int-to-byte"],
    0x8e: [base.Instruction12x, "int-to-char"],
    0x8f: [base.Instruction12x, "int-to-short"],
    0x90: [base.Instruction23x, "add-int"],
    0x91: [base.Instruction23x, "sub-int"],
    0x92: [base.Instruction23x, "mul-int"],
    0x93: [base.Instruction23x, "div-int"],
    0x94: [base.Instruction23x, "rem-int"],
    0x95: [base.Instruction23x, "and-int"],
    0x96: [base.Instruction23x, "or-int"],
    0x97: [base.Instruction23x, "xor-int"],
    0x98: [base.Instruction23x, "shl-int"],
    0x99: [base.Instruction23x, "shr-int"],
    0x9a: [base.Instruction23x, "ushr-int"],
    0x9b: [base.Instruction23x, "add-long"],
    0x9c: [base.Instruction23x, "sub-long"],
    0x9d: [base.Instruction23x, "mul-long"],
    0x9e: [base.Instruction23x, "div-long"],
    0x9f: [base.Instruction23x, "rem-long"],
    0xa0: [base.Instruction23x, "and-long"],
    0xa1: [base.Instruction23x, "or-long"],
    0xa2: [base.Instruction23x, "xor-long"],
    0xa3: [base.Instruction23x, "shl-long"],
    0xa4: [base.Instruction23x, "shr-long"],
    0xa5: [base.Instruction23x, "ushr-long"],
    0xa6: [base.Instruction23x, "add-float"],
    0xa7: [base.Instruction23x, "sub-float"],
    0xa8: [base.Instruction23x, "mul-float"],
    0xa9: [base.Instruction23x, "div-float"],
    0xaa: [base.Instruction23x, "rem-float"],
    0xab: [base.Instruction23x, "add-double"],
    0xac: [base.Instruction23x, "sub-double"],
    0xad: [base.Instruction23x, "mul-double"],
    0xae: [base.Instruction23x, "div-double"],
    0xaf: [base.Instruction23x, "rem-double"],
    0xb0: [base.Instruction12x, "add-int/2addr"],
    0xb1: [base.Instruction12x, "sub-int/2addr"],
    0xb2: [base.Instruction12x, "mul-int/2addr"],
    0xb3: [base.Instruction12x, "div-int/2addr"],
    0xb4: [base.Instruction12x, "rem-int/2addr"],
    0xb5: [base.Instruction12x, "and-int/2addr"],
    0xb6: [base.Instruction12x, "or-int/2addr"],
    0xb7: [base.Instruction12x, "xor-int/2addr"],
    0xb8: [base.Instruction12x, "shl-int/2addr"],
    0xb9: [base.Instruction12x, "shr-int/2addr"],
    0xba: [base.Instruction12x, "ushr-int/2addr"],
    0xbb: [base.Instruction12x, "add-long/2addr"],
    0xbc: [base.Instruction12x, "sub-long/2addr"],
    0xbd: [base.Instruction12x, "mul-long/2addr"],
    0xbe: [base.Instruction12x, "div-long/2addr"],
    0xbf: [base.Instruction12x, "rem-long/2addr"],
    0xc0: [base.Instruction12x, "and-long/2addr"],
    0xc1: [base.Instruction12x, "or-long/2addr"],
    0xc2: [base.Instruction12x, "xor-long/2addr"],
    0xc3: [base.Instruction12x, "shl-long/2addr"],
    0xc4: [base.Instruction12x, "shr-long/2addr"],
    0xc5: [base.Instruction12x, "ushr-long/2addr"],
    0xc6: [base.Instruction12x, "add-float/2addr"],
    0xc7: [base.Instruction12x, "sub-float/2addr"],
    0xc8: [base.Instruction12x, "mul-float/2addr"],
    0xc9: [base.Instruction12x, "div-float/2addr"],
    0xca: [base.Instruction12x, "rem-float/2addr"],
    0xcb: [base.Instruction12x, "add-double/2addr"],
    0xcc: [base.Instruction12x, "sub-double/2addr"],
    0xcd: [base.Instruction12x, "mul-double/2addr"],
    0xce: [base.Instruction12x, "div-double/2addr"],
    0xcf: [base.Instruction12x, "rem-double/2addr"],
    0xd0: [base.Instruction22s, "add-int/lit16"],
    0xd1: [base.Instruction22s, "rsub-int"],
    0xd2: [base.Instruction22s, "mul-int/lit16"],
    0xd3: [base.Instruction22s, "div-int/lit16"],
    0xd4: [base.Instruction22s, "rem-int/lit16"],
    0xd5: [base.Instruction22s, "and-int/lit16"],
    0xd6: [base.Instruction22s, "or-int/lit16"],
    0xd7: [base.Instruction22s, "xor-int/lit16"],
    0xd8: [base.Instruction22b, "add-int/lit8"],
    0xd9: [base.Instruction22b, "rsub-int/lit8"],
    0xda: [base.Instruction22b, "mul-int/lit8"],
    0xdb: [base.Instruction22b, "div-int/lit8"],
    0xdc: [base.Instruction22b, "rem-int/lit8"],
    0xdd: [base.Instruction22b, "and-int/lit8"],
    0xde: [base.Instruction22b, "or-int/lit8"],
    0xdf: [base.Instruction22b, "xor-int/lit8"],
    0xe0: [base.Instruction22b, "shl-int/lit8"],
    0xe1: [base.Instruction22b, "shr-int/lit8"],
    0xe2: [base.Instruction22b, "ushr-int/lit8"],
    # unused
    
    # for odex
    0xfa: [base.Instruction35ms, "invoke-polymorphic", INSTRUCT_TYPE_CALL_METHOD, INSTRUCT_TYPE_CALL_PROTO],
    0xfb: [base.Instruction3rms, "invoke-custom", INSTRUCT_TYPE_CALL_METHOD, INSTRUCT_TYPE_CALL_PROTO],
    0xfc: [base.Instruction22c, "invoke-polymorphic/range", INSTRUCT_TYPE_CALL_SITE],
    0xfd: [base.Instruction21c, "invoke-custom/range", INSTRUCT_TYPE_CALL_SITE],
    0xfe: [base.Instruction21c, "const-method-handle", INSTRUCT_TYPE_METHOD_HANDLE],
    0xff: [base.Instruction21c, "const-method-type", INSTRUCT_TYPE_PROTO],
}