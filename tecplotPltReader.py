#!/usr/bin/env python3
#%%
import construct
import numpy as np
import logging
import struct
from enum import IntEnum
logging.basicConfig(format='%(levelname)s %(threadName)s : %(message)s',level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

class ZoneType(IntEnum):
    ORDERED = 0
    FELINESEG = 1
    FETRIANGLE = 2
    FEQUADRILATERAL = 3
    FETETRAHEDRON = 4
    FEBRICK = 5
    FEPOLYGON = 6
    FEPOLYHEDRON = 7

FEMNumNode = {
    ZoneType.FELINESEG: 2,
    ZoneType.FETRIANGLE: 3,
    ZoneType.FEQUADRILATERAL: 4,
    ZoneType.FEBRICK: 8,
    ZoneType.FETETRAHEDRON: 4
}

def read_tec_str(byte_list):
    if not len(byte_list) == 4:
        return {'Correct' : False}

    check = construct.Int32ul.parse(byte_list)
    if not check == 0:
        return {'Correct':True, 'str': chr(byte_list[0]), 'End':False}
    return {'Correct':True, 'str': '','End':True}


def construct_qword(byte_list):
    if len(byte_list) < 8:
        return  {'Correct':False}
    qword=0
    uni_chars=''

    tec_str = ''
    first = read_tec_str(byte_list[0:4])
    second = read_tec_str(byte_list[4:8])
    if first['Correct']:
        tec_str=tec_str+first['str']
    if second['Correct']:
        tec_str=tec_str+second['str']


    for i in range(8):
        shiftval=(7-1*i)*8
        qword=qword + (byte_list[i] << shiftval)
        uni_chars=uni_chars+str(chr(byte_list[i]))

    lei32=construct.Int32sl.parse(byte_list)


    return {'Correct':True, 'qword':qword,'I32ul':lei32,
            'uni_chars':uni_chars, 'tec_str':tec_str}


def read_magic_number(byte_list):
    if len(byte_list) < 8:
        return {'Correct':False}
    magic_num = construct_qword(byte_list[0:8])
    return magic_num


def get_title(byte_list, offset=0):
    title = ''
    title_end = False
    counter = 0
    next_rel_byte = 0
    while not title_end:
        first_rel_byte = counter * 8
        next_rel_byte = (counter + 1) * 8
        first = read_tec_str(byte_list[first_rel_byte:first_rel_byte+4])
        second = read_tec_str(byte_list[first_rel_byte+4:first_rel_byte + 8])
        if not first['Correct']:
            return {'Correct':False}
        if not second['Correct']:
            return {'Correct':False}
        if first['End']:
            title_end = True
            next_rel_byte = first_rel_byte+4
            continue
        title = title + first['str']
        if second['End']:
            title_end = True
            next_rel_byte = first_rel_byte+8
            continue
        title = title + second['str']
        counter = counter+1

    return {'Correct':True,'title':title,'next_byte':next_rel_byte}

def read_var_names(byte_list, num_vars):
    var_names = list()
    next_byte=0
    for i in range(num_vars):
        qword = get_title(byte_list[next_byte:])
        if not qword['Correct']:
            return {'Correct':False}
        var_names.append(qword['title'])
        next_byte = next_byte + qword['next_byte']


    return var_names, next_byte

def parse_zone(byte_list, num_vars):
    zone={}
    zone_name = get_title(byte_list)
    if zone_name['Correct']==False:
        return {'Correct':False}

    zone['ZoneName'] =  zone_name['title']

    byte_start = zone_name['next_byte']
    byte_end = zone_name['next_byte']+4

    zone['ParentZone']= construct.Int32sl.parse(
        byte_list[byte_start:byte_end])

    byte_start = byte_start+4
    byte_end = byte_end + 4

    zone['StrandID'] = construct.Int32sl.parse(
        byte_list[byte_start:byte_end])

    byte_start = byte_end
    byte_end = byte_end + 8

    zone['SolutionTime'] = construct.Float64l.parse(
        byte_list[byte_start:byte_end])

    byte_start = byte_end
    byte_end = byte_end + 4

    zone['NotUsed'] = construct.Int32sl.parse(
        byte_list[byte_start:byte_end])

    byte_start = byte_start + 4
    byte_end = byte_end + 4

    zone['ZoneType'] = ZoneType(construct.Int32sl.parse(
        byte_list[byte_start:byte_end]))

    byte_start = byte_start + 4
    byte_end = byte_end + 4

    zone['VarLoc'] = construct.Int32sl.parse(
        byte_list[byte_start:byte_end])
    zone['VarLocs'] = [0]*num_vars


    if zone['VarLoc'] == 1:
        byte_start = byte_start + 4
        byte_end = byte_end + 4
        varLocs=[]
        for i in range(num_vars):
            byte_start = byte_start + i*4
            byte_end = byte_end + i*4
            varLocs.append(
                           construct.Int32sl.parse(
                           byte_list[byte_start:byte_end])
                          )
        zone['VarLocs'] = varLocs


    byte_start = byte_start + 4
    byte_end = byte_end + 4
    zone['RawFaceNeighbors'] = construct.Int32sl.parse(
        byte_list[byte_start:byte_end])


    byte_start = byte_start + 4
    byte_end = byte_end + 4
    zone['UserdefinedFaceNeighbors'] = construct.Int32sl.parse(
        byte_list[byte_start:byte_end])



    if zone['ZoneType'] != ZoneType.ORDERED:
        byte_start = byte_start + 4
        byte_end = byte_end + 4
        zone['RawFaceNeighbors'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

    if zone['ZoneType'] == ZoneType.ORDERED:
        byte_start = byte_start + 4
        byte_end = byte_end + 4
        zone['Imax'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

        byte_start = byte_start + 4
        byte_end = byte_end + 4
        zone['Jmax'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

        byte_start = byte_start + 4
        byte_end = byte_end + 4
        zone['Kmax'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])
    else:
        byte_start += 4
        byte_end += 4
        zone['NumPts'] = construct.Int32sl.parse(byte_list[byte_start:byte_end])
        if zone['ZoneType'] in [ZoneType.FEPOLYGON, ZoneType.FEPOLYHEDRON]:
            raise ValueError('Unsupported FEM type')

        byte_start += 4
        byte_end += 4
        zone['NumElements'] = construct.Int32sl.parse(byte_list[byte_start:byte_end])

        byte_start += 4
        byte_end += 4
        zone['ICellDim'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

        byte_start += 4
        byte_end += 4
        zone['JCellDim'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

        byte_start += 4
        byte_end += 4
        zone['KCellDim'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])

    byte_start = byte_start + 4
    byte_end = byte_end + 4
    zone['AuxdataNamePair'] = construct.Int32sl.parse(
            byte_list[byte_start:byte_end])
    return zone



def find_zones(byte_list, eo_header):
    counter = 0
    end_of_header = False
    zone_makers = list()
    while not end_of_header:
        first_byte = counter * 4
        if first_byte >= eo_header:
            end_of_header = True
            continue

        next_byte = (counter + 1) * 4
        zone_marker = construct.Float32l.parse(byte_list[first_byte:next_byte])
        if zone_marker == 299.0:
            logging.debug('Zone Found')
            logging.debug(first_byte)
            zone_makers.append(first_byte)
        counter = counter + 1

    return zone_makers

def find_end_of_header(byte_list):
    end_of_header_found = False
    counter = 0
    while not end_of_header_found:
        first_byte = counter * 4
        eo_of_header_byte = first_byte +4
        eof_value = construct.Float32l.parse(byte_list[first_byte:eo_of_header_byte])
        if eof_value == 357.0:
            end_of_header_found = True

        counter = counter +1
    return eo_of_header_byte

def read_header(byte_list):
    file_type_name=['FULL','GRID','SOLUTION']

    magic_num = read_magic_number(byte_list[0:8])
    if not magic_num['Correct']:
        return {'Correct':False}

    byte_order = construct.Int16sl.parse(byte_list[8:12])
    file_type = construct.Int16sl.parse(byte_list[12:16])


    title=''
    title_res = get_title(byte_list[16:])
    if title_res['Correct']:
        title=title_res['title']


    num_vars = construct.Int32sl.parse( byte_list[
                                        title_res['next_byte']+16:
                                        (title_res['next_byte']+20)])

    start=title_res['next_byte']+20
    var_names, next_byte = read_var_names(byte_list[start:],
                               num_vars)

    start = start + next_byte
    end_of_header = find_end_of_header(byte_list[start:])
    end_of_header_abs = end_of_header + start

    zone_markers= find_zones(byte_list[start:], end_of_header)

    zones=list()
    for zone in zone_markers:
        zones.append(parse_zone(byte_list[start+zone+4:], len(var_names)))

    # Now find and read zones
    #zones = find_zones(byte_list[next_byte+start:])

    return {'Correct': True,
            'magic_num' : magic_num,
            'ByteOrder' : byte_order,
            'FileType'  : file_type_name[file_type],
            'Title':title,
            'NumVars':num_vars,
            'VarNames':var_names,
            'EofHeader': end_of_header_abs,
            'ZoneMarkers': zone_markers,
            'Zones': zones}

def find_zones_data(byte_list, num_zones, offset):
    count_zones=0
    counter = 0
    all_zones_found = False
    zone_makers = list()
    while not all_zones_found:
        first_byte = counter * 4
        if count_zones == num_zones:
            all_zones_found = True
            continue

        next_byte = (counter + 1) * 4
        zone_marker = construct.Float32l.parse(byte_list[first_byte:next_byte])
        if zone_marker == 299.0:
            count_zones = count_zones + 1
            zone_makers.append(first_byte+offset)
        counter = counter + 1
    return zone_makers

def read_zones(byte_list, zone_markers, header):
    var_names = header['VarNames']
    var_dict = {}
    zone_vars = list()
    start_byte = 0
    zone_counter = 0
    zones_list=[]
    for zone in zone_markers:
        zone_data={}
        if construct.Float32l.parse(byte_list[zone:zone+4]) != 299.0:
            raise ValueError('Wrong zone header')
        start_byte = zone + 4
        var_dict = {}
        for name in var_names:
            end_byte = start_byte + 4
            var_dict[name] = construct.Int32sl.parse(byte_list[start_byte:end_byte])
            start_byte = end_byte
        zone_data['VarDict'] = var_dict

        zone_data['PassiveVars'] = construct.Int32sl.parse(byte_list[start_byte:start_byte + 4])
        start_byte += 4
        if zone_data['PassiveVars']  != 0:
            passive_var_dict={}
            for name in var_names:
                end_byte = start_byte + 4
                passive_var_dict[name] = construct.Int32sl.parse(byte_list[start_byte:end_byte])
                start_byte = end_byte
            zone_data['PassiveVarDict'] = passive_var_dict

        zone_data['VarSharing'] = construct.Int32sl.parse(byte_list[start_byte:start_byte + 4])
        start_byte += 4
        if zone_data['VarSharing']  != 0:
            share_var_dict={}
            for name in var_names:
                end_byte = start_byte + 4
                share_var_dict[name] = construct.Int32sl.parse(byte_list[start_byte:end_byte])
                start_byte = end_byte
            zone_data['ShareVarDict'] = share_var_dict
        else:
            d = {}
            for name in var_names:
                d[name] = -1
            zone_data['ShareVarDict'] = d

        zone_data['ConnSharing'] = construct.Int32sl.parse(byte_list[start_byte:start_byte + 4])
        start_byte=start_byte+4
        non_passive_non_shared = list()

        if zone_data['VarSharing'] !=0:
            for name in var_names:
                if zone_data['ShareVarDict'][name] == -1:
                    non_passive_non_shared.append(name)
        else:
            for name in var_names:
                non_passive_non_shared.append(name)


        if zone_data['PassiveVars'] !=0:
            for name in var_names:
                if zone_data['PassiveVarDict'][name] != 0:
                    if name in non_passive_non_shared:
                        non_passive_non_shared.remove(name)

        min_val = {}
        max_val = {}
        for var_with_min_max in non_passive_non_shared:
            end_byte = start_byte + 8
            min_val[var_with_min_max] = construct.Float64l.parse(byte_list[start_byte:end_byte])
            start_byte = end_byte

            end_byte = start_byte + 8
            max_val[var_with_min_max] = construct.Float64l.parse(byte_list[start_byte:end_byte])
            start_byte = end_byte

        logging.debug('start_data_list')
        logging.debug(start_byte)

        zone_data['Min_Vals'] = min_val
        zone_data['Max_Vals'] = max_val


        zt = header['Zones'][zone_counter]['ZoneType']
        for ivar, name in enumerate(non_passive_non_shared):
            if zt == ZoneType.ORDERED:
                Imax = header['Zones'][zone_counter]['Imax']
                Jmax = header['Zones'][zone_counter]['Jmax']
                Kmax = header['Zones'][zone_counter]['Kmax']
                if header['Zones'][zone_counter]['VarLocs'][ivar] == 0:
                    ndata = Imax * Jmax * Kmax
                else:
                    ndata = Imax * Jmax * (Kmax-1)
            else:
                NumPts = header['Zones'][zone_counter]['NumPts']
                NumElements = header['Zones'][zone_counter]['NumElements']
                if header['Zones'][zone_counter]['VarLocs'][ivar] == 0:
                    ndata = NumPts
                else:
                    ndata = NumElements

            data = np.frombuffer(byte_list, dtype='float32',
                            count=ndata,
                            offset=start_byte)
            start_byte = start_byte + 4 * ndata
            end_byte = start_byte
            zone_data[name] = data


        if zt != ZoneType.ORDERED:
            if zt not in FEMNumNode.keys():
                raise ValueError('Unsupported FEM type')
            NumPts = header['Zones'][zone_counter]['NumPts']
            NumElements = header['Zones'][zone_counter]['NumElements']
            connect = np.frombuffer(byte_list, dtype='float32',
                            count=NumElements * FEMNumNode[zt],
                            offset=start_byte)
            start_byte = start_byte + NumElements * FEMNumNode[zt]
            end_byte = start_byte
            zone_data['connect'] = connect


        zone_data['StartByte'] = zone
        zone_data['EndByte'] = end_byte

            #var_data=list()
            #for I in range(0, Imax):
            #    for J in range(0, Jmax):
            #        for K in range(0, Kmax):
            #            end_byte = start_byte + 4
                        #logging.debug(byte_list[start_byte:end_byte])
                        #logging.debug(construct.Float32l.parse(byte_list[start_byte:end_byte]))
            #            var_data.append( construct.Float32b.parse(byte_list[start_byte:end_byte]))
            #            start_byte = end_byte

     #       for J in range(0, Jmax):
     #           end_byte = start_byte + 4
     #           #logging.debug(construct.Float32l.parse(byte_list[start_byte:end_byte]))
     #           var_data.append(construct.Float32b.parse(byte_list[start_byte:end_byte]))
     #           start_byte = end_byte

     #       for K in range(0, Kmax):
     #           end_byte = start_byte + 4
     #           #logging.debug(construct.Float32l.parse(byte_list[start_byte:end_byte]))
     #           var_data.append(construct.Float32b.parse(byte_list[start_byte:end_byte]))
     #           start_byte = end_byte



        zones_list.append(zone_data)

        logging.debug('start_data_list')
        logging.debug(start_byte)
        zone_counter = zone_counter + 1

    return zones_list


def read_data_slow(byte_list, header):
    eo_header = header['EofHeader']
    num_zones = len(header['ZoneMarkers'])
    zone_markers = find_zones_data(byte_list[eo_header:], num_zones, eo_header)

    zones_list = read_zones(byte_list, zone_markers, header)
    for izone in range(len(header['Zones'])):
        if zones_list[izone]['VarSharing'] == 1:
            for k, i in zones_list[izone]['ShareVarDict'].items():
                zones_list[izone][k] = zones_list[i][k]
    return {'ZoneMarkers':zone_markers,
            'Zones':zones_list}


def read_data(byte_list, header):
    eo_header = header['EofHeader']
    num_zones = len(header['Zones'])

    reach_data_section = False
    ibyte = eo_header
    while not reach_data_section:
        zone_marker = construct.Float32l.parse(byte_list[ibyte:ibyte+4])
        if zone_marker == 299.0:
            break
        ibyte += 4

    start_byte = ibyte
    zones_list = []
    zone_markers = []
    for izone in range(len(header['Zones'])):
        zone_markers.append(start_byte)
        r = read_zones(byte_list, [start_byte], header)
        start_byte = r[0]['EndByte']
        zones_list.append(r[0])

    # Handle VarSharing
    for izone in range(len(header['Zones'])):
        if zones_list[izone]['VarSharing'] == 1:
            for k, i in zones_list[izone]['ShareVarDict'].items():
                zones_list[izone][k] = zones_list[i][k]

    return {'ZoneMarkers':zone_markers, 'Zones':zones_list}


# %%
if __name__ == "__main__":
    file = '01_ID12H15_lumped_01_crtrs_movie.dat'
    with open(file, 'rb') as f:
        byte_list = f.read()
    header = read_header(byte_list)
    data = read_data(byte_list, header)
