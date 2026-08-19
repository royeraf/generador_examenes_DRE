export interface Opcion {
  letra: string
  valor?: string
  texto: string
}

export interface Pregunta {
  numero: number
  enunciado: string
  opciones: Opcion[]
  nivel?: string
  desempeno_codigo?: string
}
