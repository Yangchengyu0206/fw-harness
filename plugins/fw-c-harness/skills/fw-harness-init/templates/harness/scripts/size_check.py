"""Size budget from Berkeley-format size output (for example arm-none-eabi-size): flash = text + data, RAM = data + bss."""


def parse_berkeley(output):
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 3 and all(field.isdigit() for field in fields[:3]):
            return int(fields[0]), int(fields[1]), int(fields[2])
    raise ValueError("could not find text/data/bss numbers in the size output")


def evaluate(text, data, bss, flash_budget, ram_budget):
    flash, ram = text + data, data + bss
    problems = []
    if flash > flash_budget:
        problems.append(f"flash {flash} B exceeds the {flash_budget} B budget")
    if ram > ram_budget:
        problems.append(f"RAM {ram} B exceeds the {ram_budget} B budget")
    summary = (f"flash {flash}/{flash_budget} B ({flash * 100 // flash_budget}%), "
               f"RAM {ram}/{ram_budget} B ({ram * 100 // ram_budget}%)")
    return problems, summary
