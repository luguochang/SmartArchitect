export type NodeShape =
  // BPMN shapes
  | "start-event"
  | "end-event"
  | "intermediate-event"
  | "task"
  // Basic shapes
  | "rectangle"
  | "rounded-rectangle"
  | "circle"
  | "diamond"
  | "hexagon"
  | "triangle"
  | "parallelogram"
  | "trapezoid"
  | "star"
  | "cloud"
  | "cylinder"
  | "document"
  // Flowchart
  | "start"
  | "end"
  | "process"
  | "decision"
  | "data"
  | "subprocess"
  | "delay"
  | "merge"
  | "manual-input"
  | "manual-operation"
  | "preparation"
  | "or"
  // Container
  | "container"
  | "frame"
  | "swimlane-horizontal"
  | "swimlane-vertical"
  | "note"
  | "folder"
  | "package"
  // User/Device
  | "user"
  | "users"
  | "mobile"
  | "desktop"
  | "tablet"
  | "iot"
  | "network"
  // BPMN specific
  | "bpmn-start-event"
  | "bpmn-end-event"
  | "bpmn-task"
  | "bpmn-gateway"
  | "bpmn-intermediate-event"
  | "bpmn-subprocess";

type ShapeConfig = {
  width?: string;
  height?: string;
  padding?: string;
  className?: string;
  borderWidth?: string;
  ringGap?: string;
  renderMethod?: "css" | "svg"; // How to render the shape
};

export const SHAPE_CONFIG: Record<NodeShape, ShapeConfig> = {
  // BPMN Events
  "start-event": {
    width: "56px",
    height: "56px",
    borderWidth: "2px",
    renderMethod: "css",
  },
  "end-event": {
    width: "56px",
    height: "56px",
    borderWidth: "4px",
    renderMethod: "css",
  },
  "intermediate-event": {
    width: "56px",
    height: "56px",
    borderWidth: "2px",
    ringGap: "5px",
    renderMethod: "css",
  },
  task: {
    width: "140px",
    height: "80px",
    borderWidth: "2px",
    className: "glass-node rounded-xl bg-white",
    renderMethod: "css",
  },

  // Basic shapes
  rectangle: {
    width: "180px",
    height: "90px",
    padding: "px-4 py-3",
    className: "glass-node rounded-lg bg-white",
    renderMethod: "css",
  },
  "rounded-rectangle": {
    width: "180px",
    height: "90px",
    padding: "px-4 py-3",
    className: "glass-node rounded-2xl bg-white",
    renderMethod: "css",
  },
  circle: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-full flex items-center justify-center",
    borderWidth: "2px",
    renderMethod: "css",
  },
  diamond: {
    width: "100px",
    height: "100px",
    className: "",  // No className for SVG shapes
    borderWidth: "2px",
    renderMethod: "svg",
  },
  hexagon: {
    width: "120px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  triangle: {
    width: "100px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  parallelogram: {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  trapezoid: {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  star: {
    width: "100px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  cloud: {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  cylinder: {
    width: "100px",
    height: "120px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  document: {
    width: "120px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },

  // Flowchart (map to basic shapes or BPMN)
  start: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-full flex items-center justify-center",
    borderWidth: "2px",
    renderMethod: "css",
  },
  end: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-full flex items-center justify-center",
    borderWidth: "3px",
    renderMethod: "css",
  },
  process: {
    width: "140px",
    height: "80px",
    padding: "px-4 py-3",
    className: "glass-node rounded-lg bg-white",
    renderMethod: "css",
  },
  decision: {
    width: "100px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  data: {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  subprocess: {
    width: "140px",
    height: "80px",
    padding: "px-3 py-2",
    className: "glass-node rounded-xl bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },
  delay: {
    width: "100px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  merge: {
    width: "80px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  "manual-input": {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  "manual-operation": {
    width: "140px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  preparation: {
    width: "120px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  or: {
    width: "100px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },

  // Container (render as rectangles with special styling)
  container: {
    width: "300px",
    height: "200px",
    padding: "p-4",
    className: "glass-node rounded-lg bg-white/50",
    borderWidth: "2px",
    renderMethod: "css",
  },
  frame: {
    width: "300px",
    height: "200px",
    padding: "p-4",
    className: "glass-node rounded-lg bg-transparent",
    borderWidth: "2px",
    renderMethod: "css",
  },
  "swimlane-horizontal": {
    width: "400px",
    height: "100px",
    padding: "p-3",
    className: "glass-node rounded-lg bg-white/30",
    borderWidth: "2px",
    renderMethod: "css",
  },
  "swimlane-vertical": {
    width: "100px",
    height: "400px",
    padding: "p-3",
    className: "glass-node rounded-lg bg-white/30",
    borderWidth: "2px",
    renderMethod: "css",
  },
  note: {
    width: "140px",
    height: "100px",
    padding: "p-3",
    className: "glass-node rounded-lg bg-yellow-50",
    borderWidth: "1px",
    renderMethod: "css",
  },
  folder: {
    width: "120px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  package: {
    width: "120px",
    height: "100px",
    padding: "p-3",
    className: "glass-node rounded-lg bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },

  // User/Device (render as circles or rectangles)
  user: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-full flex items-center justify-center",
    borderWidth: "2px",
    renderMethod: "css",
  },
  users: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-full flex items-center justify-center",
    borderWidth: "2px",
    renderMethod: "css",
  },
  mobile: {
    width: "70px",
    height: "110px",
    padding: "p-2",
    className: "glass-node rounded-2xl bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },
  desktop: {
    width: "120px",
    height: "90px",
    padding: "p-2",
    className: "glass-node rounded-lg bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },
  tablet: {
    width: "100px",
    height: "120px",
    padding: "p-2",
    className: "glass-node rounded-xl bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },
  iot: {
    width: "80px",
    height: "80px",
    className: "glass-node bg-white rounded-lg flex items-center justify-center",
    borderWidth: "2px",
    renderMethod: "css",
  },
  network: {
    width: "100px",
    height: "100px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },

  // BPMN specific (same as above but explicit)
  "bpmn-start-event": {
    width: "56px",
    height: "56px",
    borderWidth: "2px",
    renderMethod: "css",
  },
  "bpmn-end-event": {
    width: "56px",
    height: "56px",
    borderWidth: "4px",
    renderMethod: "css",
  },
  "bpmn-task": {
    width: "140px",
    height: "80px",
    borderWidth: "2px",
    padding: "px-4 py-3",
    className: "glass-node rounded-xl bg-white",
    renderMethod: "css",
  },
  "bpmn-gateway": {
    width: "80px",
    height: "80px",
    className: "",
    borderWidth: "2px",
    renderMethod: "svg",
  },
  "bpmn-intermediate-event": {
    width: "56px",
    height: "56px",
    borderWidth: "2px",
    ringGap: "5px",
    renderMethod: "css",
  },
  "bpmn-subprocess": {
    width: "140px",
    height: "80px",
    padding: "px-4 py-3",
    className: "glass-node rounded-xl bg-white",
    borderWidth: "2px",
    renderMethod: "css",
  },
};
