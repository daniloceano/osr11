export type Status = 'done' | 'in-progress' | 'planned';

export interface DataSource {
  id: string;
  name: string;
  shortName: string;
  description: string;
  variables: string[];
  resolution: string;
  period: string;
  role: string;
  stage: string;
  status: Status;
}

export interface MethodStep {
  id: string;
  label: string;
  description: string;
  status: Status;
  isCurrent?: boolean;
}

export interface ResultCard {
  id: string;
  title: string;
  subtitle: string;
  status: Status;
  description: string;
  rationale: string;
  outputs: string[];
  href?: string;
  parts?: string[];
}

export interface FigureItem {
  filename: string;
  title: string;
  caption: string;
  group: string;
  part: string;
}

export interface ProjectObjective {
  label: string;
  description: string;
}

export interface TimelinePhase {
  id: string;
  label: string;
  description: string;
  status: Status;
  tasks: string[];
}
