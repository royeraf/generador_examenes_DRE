
export interface GradoCreate {
  nombre: string;
  numero: number;
  nivel: string;
  orden: number;
}

export type GradoUpdate = Partial<GradoCreate>;

export interface CapacidadCreate {
  nombre: string;
  tipo: string;
  descripcion?: string;
}

export type CapacidadUpdate = Partial<CapacidadCreate>;

export interface DesempenoCreate {
  codigo: string;
  descripcion: string;
  grado_id: number;
  capacidad_id: number;
}

export type DesempenoUpdate = Partial<DesempenoCreate>;
