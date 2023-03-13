#!/usr/bin/python3
# -*- coding: utf-8 -*-
def update_from_dict(class_instance, defaultvalue_dictionary):
    for key, value in defaultvalue_dictionary.items():
        if hasattr(class_instance, key):
            setattr(class_instance, key, value)
        else:
            raise ValueError(f"{key} is not a valid member of the Judge class")
    