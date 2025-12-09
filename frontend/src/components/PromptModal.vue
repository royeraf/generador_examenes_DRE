<script setup lang="ts">
import { ref } from 'vue';
import {
    X,
    Copy,
    Check,
    ExternalLink,
    Sparkles,
    MessageSquare,
    Bot,
    Lightbulb
} from 'lucide-vue-next';

const props = defineProps<{
    isOpen: boolean;
    promptText: string;
}>();

const emit = defineEmits<{
    (e: 'close'): void;
}>();

const copied = ref(false);

const copyPrompt = async () => {
    try {
        await navigator.clipboard.writeText(props.promptText);
        copied.value = true;
        setTimeout(() => {
            copied.value = false;
        }, 2000);
    } catch (err) {
        console.error('Error al copiar:', err);
    }
};

const platforms = [
    {
        name: 'ChatGPT',
        icon: MessageSquare,
        color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
        url: 'https://chat.openai.com',
        instructions: 'Abre ChatGPT, pega el prompt en el chat y presiona Enter.'
    },
    {
        name: 'Google Gemini',
        icon: Sparkles,
        color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        url: 'https://gemini.google.com',
        instructions: 'Accede a Gemini, pega el prompt y envía el mensaje.'
    },
    {
        name: 'Claude',
        icon: Bot,
        color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
        url: 'https://claude.ai',
        instructions: 'Ingresa a Claude, pega el prompt en la conversación.'
    }
];
</script>

<template>
    <Teleport to="body">
        <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0"
            enter-to-class="opacity-100" leave-active-class="transition-opacity duration-150"
            leave-from-class="opacity-100" leave-to-class="opacity-0">
            <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
                @click.self="emit('close')">
                <Transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 scale-95"
                    enter-to-class="opacity-100 scale-100" leave-active-class="transition-all duration-150"
                    leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
                    <div v-if="isOpen"
                        class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
                        <!-- Header -->
                        <div
                            class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-slate-700">
                            <div class="flex items-center gap-3">
                                <div
                                    class="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                                    <Copy class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                                </div>
                                <div>
                                    <h2 class="text-lg font-semibold text-slate-800 dark:text-white">Prompt Generado
                                    </h2>
                                    <p class="text-sm text-slate-500 dark:text-slate-400">Úsalo en tu plataforma de IA
                                        favorita</p>
                                </div>
                            </div>
                            <button @click="emit('close')"
                                class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
                                <X class="w-5 h-5 text-slate-500 dark:text-slate-400" />
                            </button>
                        </div>

                        <!-- Content -->
                        <div class="flex-1 overflow-y-auto p-6 space-y-6">

                            <!-- Instructions Section -->
                            <div
                                class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                                <div class="flex items-start gap-3">
                                    <Lightbulb
                                        class="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <h3 class="font-medium text-amber-800 dark:text-amber-300 mb-1">¿Cómo usar este
                                            prompt?</h3>
                                        <p class="text-sm text-amber-700 dark:text-amber-400">
                                            Copia el prompt y pégalo en cualquier plataforma de Inteligencia Artificial.
                                            El prompt está diseñado para generar preguntas de comprensión lectora de
                                            alta calidad.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Platforms -->
                            <div>
                                <h3 class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Plataformas
                                    recomendadas</h3>
                                <div class="grid gap-3">
                                    <a v-for="platform in platforms" :key="platform.name" :href="platform.url"
                                        target="_blank" rel="noopener noreferrer"
                                        class="flex items-center gap-4 p-4 bg-gray-50 dark:bg-slate-900 rounded-lg border border-gray-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors group">
                                        <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                                            :class="platform.color">
                                            <component :is="platform.icon" class="w-5 h-5" />
                                        </div>
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2">
                                                <span class="font-medium text-slate-800 dark:text-white">{{
                                                    platform.name }}</span>
                                                <ExternalLink
                                                    class="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                            <p class="text-sm text-slate-500 dark:text-slate-400">{{
                                                platform.instructions }}</p>
                                        </div>
                                    </a>
                                </div>
                            </div>

                            <!-- Prompt Preview -->
                            <div>
                                <h3 class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Vista previa del
                                    prompt</h3>
                                <div
                                    class="bg-gray-50 dark:bg-slate-900 rounded-lg p-4 border border-gray-200 dark:border-slate-700 max-h-48 overflow-y-auto">
                                    <pre
                                        class="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">{{ promptText }}</pre>
                                </div>
                            </div>

                            <!-- Tips -->
                            <div
                                class="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
                                <h3 class="font-medium text-indigo-800 dark:text-indigo-300 mb-2">💡 Consejos para
                                    mejores resultados</h3>
                                <ul class="text-sm text-indigo-700 dark:text-indigo-400 space-y-1.5">
                                    <li>• Si la respuesta no es satisfactoria, pide a la IA que "regenere" o "mejore" el
                                        examen.</li>
                                    <li>• Puedes solicitar más o menos preguntas según necesites.</li>
                                    <li>• Si subiste un texto base, la IA lo usará como referencia para las preguntas.
                                    </li>
                                    <li>• Revisa siempre el examen generado antes de usarlo con tus estudiantes.</li>
                                </ul>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div
                            class="px-6 py-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900">
                            <div class="flex items-center justify-between gap-4">
                                <p class="text-xs text-slate-500 dark:text-slate-400">
                                    El prompt se copiará al portapapeles
                                </p>
                                <div class="flex gap-3">
                                    <button @click="emit('close')"
                                        class="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors">
                                        Cerrar
                                    </button>
                                    <button @click="copyPrompt"
                                        class="px-5 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                                        :class="copied
                                            ? 'bg-emerald-600 text-white'
                                            : 'bg-indigo-600 hover:bg-indigo-700 text-white'">
                                        <Check v-if="copied" class="w-4 h-4" />
                                        <Copy v-else class="w-4 h-4" />
                                        {{ copied ? '¡Copiado!' : 'Copiar Prompt' }}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </Transition>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
/* Scrollbar sutil */
::-webkit-scrollbar {
    width: 4px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 20px;
}

.dark ::-webkit-scrollbar-thumb {
    background-color: #475569;
}
</style>
