export function chatScrollBehaviorFromReducedMotion(reducedMotion: boolean): ScrollBehavior {
  return reducedMotion ? "auto" : "smooth";
}

/** 新消息到达时是否平滑滚到底（尊重减弱动效）。 */
export function chatScrollBehavior(): ScrollBehavior {
  if (typeof window === "undefined") return "auto";
  return chatScrollBehaviorFromReducedMotion(
    window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
}
