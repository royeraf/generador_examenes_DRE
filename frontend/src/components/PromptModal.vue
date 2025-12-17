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
    Lightbulb,
    Globe,
    FileText,
    RefreshCw,
    BarChart3,
    BookOpen,
    CheckCircle,
    Clipboard
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
                        class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border-2 border-teal-100 dark:border-slate-700">
                        <!-- Header -->
                        <div
                            class="flex items-center justify-between px-6 py-5 bg-gradient-to-r from-teal-500 via-teal-600 to-sky-500 dark:from-slate-700 dark:via-slate-700 dark:to-slate-700">
                            <div class="flex items-center gap-4">
                                <div
                                    class="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg">
                                    <Copy class="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h2 class="text-lg font-bold text-white flex items-center gap-2">
                                        📋 Prompt Generado
                                    </h2>
                                    <p class="text-sm text-teal-100 dark:text-slate-400 font-medium">Úsalo en tu
                                        plataforma de IA
                                        favorita</p>
                                </div>
                            </div>
                            <button @click="emit('close')"
                                class="p-2 rounded-xl bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white transition-all duration-300">
                                <X class="w-5 h-5" />
                            </button>
                        </div>

                        <!-- Content -->
                        <div class="flex-1 overflow-y-auto p-6 space-y-6">

                            <!-- Instructions Section -->
                            <div
                                class="bg-gradient-to-r from-amber-50 to-orange-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800 rounded-xl p-5">
                                <div class="flex items-start gap-4">
                                    <div
                                        class="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
                                        <Lightbulb class="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h3
                                            class="font-bold text-amber-800 dark:text-amber-300 mb-2 text-lg flex items-center gap-2">
                                            <Lightbulb class="w-5 h-5" /> ¿Cómo
                                            usar este
                                            prompt?
                                        </h3>
                                        <p class="text-sm text-amber-700 dark:text-amber-400 leading-relaxed">
                                            Copia el prompt y pégalo en cualquier plataforma de Inteligencia Artificial.
                                            El prompt está diseñado para generar preguntas de comprensión lectora de
                                            alta calidad para tus estudiantes.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Platforms -->
                            <div>
                                <h3
                                    class="text-sm font-bold text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2">
                                    <Globe class="w-4 h-4" /> Plataformas recomendadas
                                </h3>
                                <div class="grid gap-3">
                                    <a v-for="platform in platforms" :key="platform.name" :href="platform.url"
                                        target="_blank" rel="noopener noreferrer"
                                        class="flex items-center gap-4 p-4 bg-white dark:bg-slate-900 rounded-xl border-2 border-gray-100 dark:border-slate-700 hover:border-teal-300 dark:hover:border-teal-700 transition-all duration-300 group hover:-translate-y-0.5 hover:shadow-lg">
                                        <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                                            :class="platform.color">
                                            <component :is="platform.icon" class="w-6 h-6" />
                                        </div>
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2">
                                                <span class="font-bold text-slate-800 dark:text-white">{{
                                                    platform.name }}</span>
                                                <ExternalLink
                                                    class="w-4 h-4 text-teal-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                            <p class="text-sm text-slate-500 dark:text-slate-400">{{
                                                platform.instructions }}</p>
                                        </div>
                                    </a>
                                </div>
                            </div>

                            <!-- Prompt Preview -->
                            <div>
                                <h3
                                    class="text-sm font-bold text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2">
                                    <FileText class="w-4 h-4" /> Vista previa del prompt
                                </h3>
                                <div
                                    class="bg-gradient-to-br from-slate-50 to-gray-50 dark:bg-slate-900 rounded-xl p-5 border-2 border-gray-200 dark:border-slate-700 max-h-48 overflow-y-auto">
                                    <pre
                                        class="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">{{ promptText }}</pre>
                                </div>
                            </div>

                            <!-- Tips -->
                            <div
                                class="bg-gradient-to-r from-teal-50 to-sky-50 dark:bg-teal-900/20 border-2 border-teal-200 dark:border-teal-800 rounded-xl p-5">
                                <h3 class="font-bold text-teal-800 dark:text-teal-300 mb-3 flex items-center gap-2">
                                    <Sparkles class="w-5 h-5" /> Consejos para mejores resultados
                                </h3>
                                <ul class="text-sm text-teal-700 dark:text-teal-400 space-y-2">
                                    <li class="flex items-start gap-2">
                                        <RefreshCw class="w-4 h-4 mt-0.5 flex-shrink-0" />Si la respuesta no es
                                        satisfactoria, pide a la IA que "regenere" o "mejore" el
                                        examen.
                                    </li>
                                    <li class="flex items-start gap-2">
                                        <BarChart3 class="w-4 h-4 mt-0.5 flex-shrink-0" /> Puedes solicitar más o menos
                                        preguntas según necesites.
                                    </li>
                                    <li class="flex items-start gap-2">
                                        <BookOpen class="w-4 h-4 mt-0.5 flex-shrink-0" /> Si subiste un texto base, la
                                        IA
                                        lo usará como referencia para las preguntas.
                                    </li>
                                    <li class="flex items-start gap-2">
                                        <CheckCircle class="w-4 h-4 mt-0.5 flex-shrink-0" /> Revisa siempre el examen
                                        generado
                                        antes de usarlo con tus estudiantes.
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div
                            class="px-6 py-5 border-t-2 border-gray-100 dark:border-slate-700 bg-gradient-to-r from-gray-50 to-slate-50 dark:from-slate-900 dark:to-slate-900">
                            <div class="flex items-center justify-between gap-4">
                                <p class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                                    <Clipboard class="w-4 h-4" /> El prompt se copiará al portapapeles
                                </p>
                                <div class="flex gap-3">
                                    <button @click="emit('close')"
                                        class="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700 transition-all duration-300 border-2 border-gray-200 dark:border-slate-600">
                                        Cerrar
                                    </button>
                                    <button @click="copyPrompt"
                                        class="px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all duration-300 shadow-lg hover:-translate-y-0.5"
                                        :class="copied
                                            ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-teal-500/30'
                                            : 'bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-600 hover:to-sky-600 text-white shadow-teal-500/30'">
                                        <Check v-if="copied" class="w-5 h-5" />
                                        <Copy v-else class="w-5 h-5" />
                                        {{ copied ? '¡Copiado! 🎉' : 'Copiar Prompt' }}
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
