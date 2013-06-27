#ifndef __platform_h__
#define __platform_h__

#include <pic12f1822.h>
#include "common_types.h"
#include "bit_utilities.h"

//Do not compile components that are needed on the pic12 to make sure the compiler doesn't choke
#define _PIC12LEAN

#endif