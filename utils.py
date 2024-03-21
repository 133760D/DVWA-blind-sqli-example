#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 25 19:27:18 2024

@author: Alexandre Maurin
"""
import os

def table2csv(table:dict, path:str, filename:str) -> None:
    if path != "" and path[-1] not in ["/", "\\", os.sep]:
        filename+=os.sep
    with open(f"{path + filename}.csv", 'w') as f:
        columns = list(table.keys())
        if columns == []: return
        f.write(','.join(columns) + '\n')
        maxlen = max([len(table[column]) for column in columns])
        for column in columns:
            table[column].extend([None] * (maxlen-len(table[column])))
        for i in range(maxlen):
            f.write(','.join([str(table[column][i]) for column in columns]) + '\n')


def top_sort(data:dict):
    """returns informations about the n top tables with the most rows"""
    top = dict()
    for table in data.keys():
        top[table] = len(list(data[table].values())[0])
    return {k: v for k, v in sorted(top.items(), key=lambda item: item[1], reverse=True)}