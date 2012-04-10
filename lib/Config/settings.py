incoming_default = {
'require_arrival_monitor': False,
'control_file_extension': 'stager-ctrl-bss',
'receipt_file_extension': 'stager-rcpt-bss',
'thankyou_file_extension': 'stager-thanks-bss',
'stop_file': '.stop'
}

outgoing_default = {
'target_uses_arrival_monitor':  False,
'control_file_extension': 'stager-ctrl-bss',
'receipt_file_extension': 'stager-rcpt-bss',
'thankyou_file_extension': 'stager-thanks-bss',
'retry_count': 3,
'stop_file': '.stop',
'stop_file_poll_interval': 600
}

