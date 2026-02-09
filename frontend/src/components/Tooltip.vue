<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
    text: string;
    position?: 'top' | 'bottom' | 'left' | 'right';
}>();

const isVisible = ref(false);
const triggerRef = ref<HTMLElement | null>(null);
const tooltipStyle = ref({
    top: '0px',
    left: '0px',
});

const show = () => {
    if (!triggerRef.value) return;

    const rect = triggerRef.value.getBoundingClientRect();
    const pos = props.position || 'top';

    let top = 0;
    let left = 0;

    switch (pos) {
        case 'top':
            top = rect.top - 8;
            left = rect.left + rect.width / 2;
            break;
        case 'bottom':
            top = rect.bottom + 8;
            left = rect.left + rect.width / 2;
            break;
        case 'left':
            top = rect.top + rect.height / 2;
            left = rect.left - 8;
            break;
        case 'right':
            top = rect.top + rect.height / 2;
            left = rect.right + 8;
            break;
    }

    tooltipStyle.value = {
        top: `${top}px`,
        left: `${left}px`,
    };

    isVisible.value = true;
};

const hide = () => {
    isVisible.value = false;
};

// Close on scroll
const handleScroll = () => {
    if (isVisible.value) {
        hide();
    }
};

onMounted(() => {
    window.addEventListener('scroll', handleScroll, true);
});

onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll, true);
});
</script>

<template>
    <div ref="triggerRef" class="tooltip-trigger" @mouseenter="show" @mouseleave="hide" @focus="show" @blur="hide">
        <slot></slot>
    </div>

    <Teleport to="body">
        <Transition name="fade">
            <div v-if="isVisible" class="tooltip-portal" :class="position || 'top'" :style="tooltipStyle"
                role="tooltip">
                <div class="tooltip-content">
                    <div class="tooltip-text">{{ text }}</div>
                    <div class="tooltip-arrow" :class="position || 'top'"></div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.tooltip-trigger {
    display: inline-flex;
    width: 100%;
}

.tooltip-portal {
    position: fixed;
    z-index: 9999;
    pointer-events: none;
}

.tooltip-portal.top {
    transform: translateX(-50%) translateY(-100%);
}

.tooltip-portal.bottom {
    transform: translateX(-50%);
}

.tooltip-portal.left {
    transform: translateX(-100%) translateY(-50%);
}

.tooltip-portal.right {
    transform: translateY(-50%);
}

.tooltip-content {
    position: relative;
    max-width: 400px;
    min-width: 200px;
    padding: 10px 14px;
    background: #0f172a;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow:
        0 20px 25px -5px rgba(0, 0, 0, 0.4),
        0 8px 10px -6px rgba(0, 0, 0, 0.3),
        0 0 0 1px rgba(0, 0, 0, 0.1);
}

.tooltip-text {
    font-size: 0.875rem;
    line-height: 1.6;
    color: #f1f5f9;
    white-space: normal;
    word-wrap: break-word;
}

.tooltip-arrow {
    position: absolute;
    width: 10px;
    height: 10px;
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-top: none;
    border-left: none;
}

.tooltip-arrow.top {
    bottom: -6px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
}

.tooltip-arrow.bottom {
    top: -6px;
    left: 50%;
    transform: translateX(-50%) rotate(-135deg);
}

.tooltip-arrow.left {
    right: -6px;
    top: 50%;
    transform: translateY(-50%) rotate(-45deg);
}

.tooltip-arrow.right {
    left: -6px;
    top: 50%;
    transform: translateY(-50%) rotate(135deg);
}

/* Transition */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.tooltip-portal.top.fade-enter-from,
.tooltip-portal.top.fade-leave-to {
    transform: translateX(-50%) translateY(calc(-100% + 4px));
}

.tooltip-portal.bottom.fade-enter-from,
.tooltip-portal.bottom.fade-leave-to {
    transform: translateX(-50%) translateY(-4px);
}

.tooltip-portal.left.fade-enter-from,
.tooltip-portal.left.fade-leave-to {
    transform: translateX(calc(-100% + 4px)) translateY(-50%);
}

.tooltip-portal.right.fade-enter-from,
.tooltip-portal.right.fade-leave-to {
    transform: translateX(-4px) translateY(-50%);
}
</style>
