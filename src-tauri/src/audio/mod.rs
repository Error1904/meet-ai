use cpal::traits::{DeviceTrait, HostTrait};

pub struct AudioEngine {
    pub is_loopback_active: bool,
}

impl AudioEngine {
    pub fn new() -> Self {
        Self { is_loopback_active: false }
    }

    pub fn list_host_devices() -> Vec<String> {
        let host = cpal::default_host();
        let mut devices = Vec::new();

        if let Ok(input_devices) = host.input_devices() {
            for dev in input_devices {
                if let Ok(name) = dev.name() {
                    devices.push(format!("Input: {}", name));
                }
            }
        }

        if let Ok(output_devices) = host.output_devices() {
            for dev in output_devices {
                if let Ok(name) = dev.name() {
                    devices.push(format!("Output/Loopback: {}", name));
                }
            }
        }

        devices
    }
}
