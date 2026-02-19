# F: B. Shapes & Containers

#### **B. Shapes & Containers** *Design Philosophy: "Softened Geometry." Sharp corners are for data; rounded corners are for processes.* **Core Components** * **Process Nodes (The Standard):** Rounded Rectangles (Corner radius 5-10 px). This is the dominant shape (~80%) for generic layers or steps. * **Tensors & Data:** * **3D Stacks/Cuboids:** Used to imply depth/volume (e.g., $B \times H \times W$). * **Flat Squares/Grids:** Used for matrices, tokens, or attention maps. * **Cylinders:** Exclusively reserved for Databases, Buffers, or Memory. **Grouping & Hierarchy** * **The "Macro-Micro" Pattern:** A solid, light-colored container represents the global view, with a specific module (e.g., "Attention Block") connected via lines to a "zoomed-in" detailed breakout box. * **Borders:** * **Solid:** For physical components. * **Dashed:** Highly prevalent for indicating "Logical Stages," " Optional Paths," or "Scopes." 26



[[PAGE \1]]

PaperBanana: Automating Academic Illustration for AI Scientists
