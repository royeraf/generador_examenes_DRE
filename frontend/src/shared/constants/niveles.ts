export type NivelDificultad = 'basico' | 'intermedio' | 'avanzado';

export interface NivelDificultadOption {
  id: NivelDificultad;
  nombre: string;
  descripcion: string;
  icono: string;
}

export const NIVELES_DIFICULTAD: NivelDificultadOption[] = [
  { id: 'basico',     nombre: 'Básico',      descripcion: 'Preguntas simples y sencillas', icono: 'Sprout' },
  { id: 'intermedio', nombre: 'Intermedio',  descripcion: 'Demanda cognitiva media',        icono: 'Leaf' },
  { id: 'avanzado',   nombre: 'Avanzado',    descripcion: 'Alta demanda cognitiva',         icono: 'TreeDeciduous' },
];
