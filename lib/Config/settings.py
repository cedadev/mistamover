global_default = {
'general_poll_interval': 3
}

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
'receipt_file_poll_count': 100,
'receipt_file_poll_interval': 5,
'stop_file': '.stop',
'stop_file_poll_interval': 600
}

