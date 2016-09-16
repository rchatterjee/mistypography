# cython: language_level=2, boundscheck=True, c_string_type=str
# cython: infer_types=True, c_string_encoding=utf-8
# cython: cdivision=True, profile=True

################################################################################
# CYTHON IS TOTAL JOKE!! NEVER USE IT
################################################################################
import numpy as np
cimport numpy as np
cimport cython
import string
np.import_array()

cdef char pw_characters[95];
for i, c in enumerate(string.printable[:-5]):
    pw_characters[i] = ord(c)

def apply_edits(char* w):
    """
    Apply all edits to w and returned the list of possible strings.
    """
    cdef int l = int(len(w))
    cdef int n = (l+1) * len(pw_characters) + (l-1) # insert, delete
    n += l * (len(pw_characters) - 1) # replace
    n += 4 # those extra modificaitons
    ret = np.chararray(n, itemsize=l+2);
    cdef i=0, j=0;

    ret[i] = w.capitalize(); i += 1
    if chr(w[0]).isupper():
        ret[i] = chr(w[0]).lower()+w[1:]
        i += 1
    ret[i] = w.swapcase(); i += 1
    cdef int k = 0
    cdef char c
    while k<len(pw_characters):
        c = pw_characters[k]; k+=1
        j = 0
        while j<l:
            ret[i] = w[:j] + chr(c) + w[j:]; i += 1  # insert
            if c != w[j]:
                ret[i] = w[:j] + chr(c) + w[j+1:]; i += 1 # replace
            j += 1
        ret[i] = w + chr(c); i += 1
    j = 0
    while j<l:
        ret[i] = w[:j] + w[j+1:]  # delete
        i += 1
        j += 1
    if i<n:
        ret = ret[:i]
    return ret[np.unique(ret, return_index=True)[1]]

# #include<stdio.h>
# #include<sttring.h>
# #include<stdlib.h>

# char allowed_chars[] = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ";
# int m = 95;
# /*
#  * Given a word w, returns a list of words that are within edit
#  * distance 1 from w
#  */
# void toggleCase(const char * string, char *ret) {
#   int i = 0;
#   while(string[i] != '\0') {
#     if(string[i]>='a' && string[i]<='z')
#       ret[i] = string[i] - 32;
#     else if(string[i]>='A' && string[i]<='Z')
#       ret[i] = string[i] + 32;
#     else
#       ret[i] = string[i];
#     i++;
#   }
# } 

# char** apply_edits(const char *w) {
#   int l = strlen(w);
#   int n = (l+1)*m + l*(m-1) + (l-1);
#   char **ret = (char*)malloc(sizeof(char*)*n);
#   int i, j;
#   ret[i] = malloc(sizeof(char)*l);
#   toggleCase(w, ret[i++]);
#   for(i=0; i<l; i++) {
#     for(j=0; j<m; j++) {
#       ret[i] = malloc(sizeof(char)*l);
#     strcpy(w, ret[i]);
    
# }
