//app_main.c

#include "platform.h"
#include "watchdog.h"
#include "sensor_defines.h"
#include "port.h"
#include "sample.h"
#include "mib12_api.h"
#include "log.h"
#include "digital_amp.h"
#include "watchdog.h"

#define _XTAL_FREQ			4000000

extern unsigned int adc_result;

void task(void)
{
	wdt_disable();

	set_analog_power(1);
	select_analog_input(kCurrentInput);

	while(1)
	{
		;
	}
}

void interrupt_handler(void)
{

}

void initialize(void)
{
	wdt_disable();

	PIN_DIR(VOLT1, INPUT);
	PIN_TYPE(VOLT1, ANALOG);

	PIN_DIR(VOLT2, INPUT);
	PIN_TYPE(VOLT2, ANALOG);
	
	PIN_DIR(VOLT3, INPUT);
	PIN_TYPE(VOLT3, ANALOG);
	
	LATCH(AN_POWER) = 0;
	//PIN_TYPE(AN_POWER, DIGITAL); AN_POWER is digital only (A6)
	PIN_DIR(AN_POWER, OUTPUT);

	LATCH(AN_SELECT) = 0;
	PIN_DIR(AN_SELECT, OUTPUT);
	PIN_TYPE(AN_SELECT, DIGITAL);

	LATCH(AN_INVERT) = 0;
	PIN_DIR(AN_INVERT, OUTPUT);
	PIN_TYPE(AN_INVERT, DIGITAL);

	LATCH(AN_PROG) = 0;
	PIN_DIR(AN_PROG, OUTPUT);
	PIN_TYPE(AN_PROG, DIGITAL);

	PIN_TYPE(AN_VOLTAGE, ANALOG);
	PIN_DIR(AN_VOLTAGE, INPUT);
}

void main()
{

}

void check_v1()
{
	sample_v1();

	mib_buffer[0] = (adc_result & 0xFF);
	mib_buffer[1] = (adc_result >> 8) & 0xFF;

	bus_slave_setreturn(pack_return_status(0, 2));
}

void check_v2()
{
	sample_v2();

	mib_buffer[0] = (adc_result & 0xFF);
	mib_buffer[1] = (adc_result >> 8) & 0xFF;

	bus_slave_setreturn(pack_return_status(0, 2));
}

void check_v3()
{
	sample_v3();

	mib_buffer[0] = (adc_result & 0xFF);
	mib_buffer[1] = (adc_result >> 8) & 0xFF;

	bus_slave_setreturn(pack_return_status(0, 2));
}

void check_voltage()
{
	sample_analog();

	mib_buffer[0] = (adc_result & 0xFF);
	mib_buffer[1] = (adc_result >> 8) & 0xFF;

	bus_slave_setreturn(pack_return_status(0, 2));
}

void set_gain1()
{
	damp_set_stage1_gain(mib_buffer[0]);
	bus_slave_setreturn(pack_return_status(0, 0));
}

void set_gain2()
{
	damp_set_stage2_gain(mib_buffer[0]);
	bus_slave_setreturn(pack_return_status(0, 0));
}

void set_offset()
{
	damp_set_offset(mib_buffer[0]);
	bus_slave_setreturn(pack_return_status(0, 0));
}