#include "sensor_mib_feature.h"
#include "sensor_manager.h"

#include "bus_slave.h"
#include "mib_definitions.h"
#include "mib_feature_definition.h"

static void log_sensor_event_mib(void)
{
	uint8 mib_addr = plist_get_int8(0);
	uint8  stream_id = plist_get_int8(1); 
	uint8  meta = plist_get_int8(2);
	uint64 *value = plist_get_buffer(3);
	
	//TODO: Lazily write to flash
	push_sensor_value( mib_addr, stream_id, meta, value );

	bus_slave_setreturn(pack_return_status(kNoMIBError, 0));
}

DEFINE_MIB_FEATURE_COMMANDS(sensor) {
	{ 0x00, log_sensor_event_mib, plist_spec(3, true) }
};
DEFINE_MIB_FEATURE(sensor);