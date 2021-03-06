# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: model_predict.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='model_predict.proto',
  package='modelpredict',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x13model_predict.proto\x12\x0cmodelpredict\"T\n\x05Usage\x12\x10\n\x08\x63puUsage\x18\x01 \x01(\x01\x12\x14\n\x0cmemeoryUsage\x18\x02 \x01(\x01\x12\x12\n\notherRules\x18\x03 \x01(\t\x12\x0f\n\x07podName\x18\x04 \x01(\t\"\x1a\n\x06\x43hoice\x12\x10\n\x08nodeName\x18\x01 \x01(\t2F\n\x0cModelPredict\x12\x36\n\x07Predict\x12\x13.modelpredict.Usage\x1a\x14.modelpredict.Choice\"\x00\x62\x06proto3'
)




_USAGE = _descriptor.Descriptor(
  name='Usage',
  full_name='modelpredict.Usage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='cpuUsage', full_name='modelpredict.Usage.cpuUsage', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='memeoryUsage', full_name='modelpredict.Usage.memeoryUsage', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='otherRules', full_name='modelpredict.Usage.otherRules', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='podName', full_name='modelpredict.Usage.podName', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=37,
  serialized_end=121,
)


_CHOICE = _descriptor.Descriptor(
  name='Choice',
  full_name='modelpredict.Choice',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='nodeName', full_name='modelpredict.Choice.nodeName', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=123,
  serialized_end=149,
)

DESCRIPTOR.message_types_by_name['Usage'] = _USAGE
DESCRIPTOR.message_types_by_name['Choice'] = _CHOICE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Usage = _reflection.GeneratedProtocolMessageType('Usage', (_message.Message,), {
  'DESCRIPTOR' : _USAGE,
  '__module__' : 'model_predict_pb2'
  # @@protoc_insertion_point(class_scope:modelpredict.Usage)
  })
_sym_db.RegisterMessage(Usage)

Choice = _reflection.GeneratedProtocolMessageType('Choice', (_message.Message,), {
  'DESCRIPTOR' : _CHOICE,
  '__module__' : 'model_predict_pb2'
  # @@protoc_insertion_point(class_scope:modelpredict.Choice)
  })
_sym_db.RegisterMessage(Choice)



_MODELPREDICT = _descriptor.ServiceDescriptor(
  name='ModelPredict',
  full_name='modelpredict.ModelPredict',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=151,
  serialized_end=221,
  methods=[
  _descriptor.MethodDescriptor(
    name='Predict',
    full_name='modelpredict.ModelPredict.Predict',
    index=0,
    containing_service=None,
    input_type=_USAGE,
    output_type=_CHOICE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_MODELPREDICT)

DESCRIPTOR.services_by_name['ModelPredict'] = _MODELPREDICT

# @@protoc_insertion_point(module_scope)
