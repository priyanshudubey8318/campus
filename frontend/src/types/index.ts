export * from "./health";
export * from "./auth";
export * from "./academic";
export * from "./pulsewatch";
export * from "./pulserisk";
export * from "./pulseassist";
export * from "./pulserecord";
export * from "./pulsecase";

export type Role =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "FACULTY"
  | "ADVISOR"
  | "COUNSELOR"
  | "STUDENT"
  | "AUTHORIZED_REPORTER";

export interface SystemModule {
  id: string;
  name: string;
  code: string;
  description: string;
  status: "Planned" | "Foundation Ready" | "Active";
  phase: number;
}
