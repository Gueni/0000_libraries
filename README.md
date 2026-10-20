# 0000_libraries

Personal electronics design libraries for **Altium Designer** and **PLECS**:
schematic symbols, PCB footprints, a database-backed parts library, PLECS
component libraries, semiconductor thermal/loss models, and a set of Altium
tutorial projects.

```
0000_libraries/
├── Altium/
│   ├── DATABASE.DbLib    # Database library (links to DB.mdb)
│   ├── DB.mdb            # Parts database (MS Access)
│   ├── SCH.SchLib        # Schematic symbols
│   ├── FTP.PcbLib        # PCB footprints
│   └── TUT/              # Tutorial guides + example projects
└── Plecs/
    ├── *.plecs           # PLECS component libraries
    └── Thermal Lib/      # Semiconductor thermal/loss models (XML)
```

---

## Altium Designer

### Libraries

| File | Description |
| --- | --- |
| [DATABASE.DbLib](Altium/DATABASE.DbLib) | Database library that maps DB records to symbols and footprints. |
| [DB.mdb](Altium/DB.mdb) | Parts database. Tables: Capacitors, Connectors, Crystal, Diodes, Ferrit Bead, Integrated Circuits, LED, Light Pipe, PCB, Resistors, Switches, Transformers, Transistors. |
| [SCH.SchLib](Altium/SCH.SchLib) | Schematic symbol library. |
| [FTP.PcbLib](Altium/FTP.PcbLib) | PCB footprint library. |

### Setup

The DbLib uses an **absolute path** to the database:

```
0000_libraries\Altium\DB.mdb
```

If you clone the repo anywhere else:

1. Open `DATABASE.DbLib` in Altium.
2. Point the connection at your local `Altium\DB.mdb` (this updates both
   `ConnectionString` and `LibraryDatabasePath`), or enable the relative-path
   option (`DatabasePathRelative`).
3. Make sure `SCH.SchLib` and `FTP.PcbLib` are reachable from the DbLib's
   search paths.

The connection uses the `Microsoft.ACE.OLEDB.12.0` provider. If Altium can't
connect, install the **Microsoft Access Database Engine** matching Altium's
bitness (64-bit for current versions).

### Tutorials

[`Altium/TUT/`](Altium/TUT/) contains one folder per topic, usually with a PDF
guide and an example project (`.PrjPcb`). Read the PDF, then open the project.

| Layout & routing | Design structure | Rules & manufacturing |
| --- | --- | --- |
| Active Route | Board Level Annotation | Back Drill |
| Differential Pair Routing with Impedance Profile | Creating Classes from Schematic | Clearance Checking in 3D |
| Length Tuning Routing | Multi-Channel Design | Design Rule Queries |
| Re-Routing | Working with Rooms in a Multi-Channel Design | Defining the Board Shape from a 3D Model |
| Pin Swapping | Using Design Variants | Creating Multiple Layer Stacks (Adv Mode) |
| Teardrops | Using Signal Harnesses | Rigid-Flex Design Advanced Mode |
| Via Stitching and Via Shielding | Using Snippets with Design Reuse Panel | Embedded Board Array |
| Using xSignals in a High-Speed Design | Project Templates | Draftsman Templates |
| Using xSignals in a High-Speed Design with Diff Pair | | Testpoint |

---

## PLECS

### Component libraries

| File | Description |
| --- | --- |
| [CTRL.plecs](Plecs/CTRL.plecs) | Control blocks |
| [Magnatic Components.plecs](Plecs/Magnatic%20Components.plecs) | Magnetic components |
| [Passives.plecs](Plecs/Passives.plecs) | Passive components |
| [Power.plecs](Plecs/Power.plecs) | Power-stage components |
| [Sensors.plecs](Plecs/Sensors.plecs) | Sensors |
| [Snubbers.plecs](Plecs/Snubbers.plecs) | Snubber circuits |
| [Switches.plecs](Plecs/Switches.plecs) | Switches |

Open a library in PLECS (or add it to the library browser) and drag components
into your model.

### Thermal library

[`Plecs/Thermal Lib/`](Plecs/Thermal%20Lib/) holds **372** semiconductor
models in the PLEXIM semiconductor XML format, with conduction and switching
loss data plus thermal impedance, for use with the PLECS thermal domain.

| Vendor | Models | Examples |
| --- | ---: | --- |
| Wolfspeed | 299 | C2M/C3M/E3M SiC MOSFETs, C3D–C6D/E3D/E4D SiC diodes, CAB/CAS/CBB/CCB/CCS/WAB power modules |
| Microchip | 53 | MSC SiC MOSFETs and Schottky diodes |
| GaN Systems | 11 | GS61xxx, GS665xx, GS-065 GaN HEMTs |
| Infineon | 5 | AIMDQ75R CoolSiC MOSFETs |
| Texas Instruments | 3 | LMG342x, LMG352x GaN |
| ROHM | 1 | SCT3060AW7 |

By type: 232 diodes, 124 MOSFETs, 13 MOSFETs with integrated diode, 3 TI GaN.

**Naming:** files are named by part number. For MOSFETs with a separate diode
model, the diode lives in a sibling file with a `_bodydiode`,
`_schottkydiode`, or `_diode` suffix, e.g. `WAB300M12BM3.xml` and
`WAB300M12BM3_bodydiode.xml`.

**Usage:** in PLECS, open the thermal library browser and add the
`Thermal Lib` folder (or import individual files), then reference the part
number from a device's thermal description. Many MOSFET models expose `Rgon` /
`Rgoff` (external gate resistance) as variables.

---
