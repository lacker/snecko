#!/usr/bin/env python
# A smoke test to see if CUDA is set up ok.

import torch

print("checking torch GPU bindings...")
print(torch.cuda.get_device_name(0))
print("done")
