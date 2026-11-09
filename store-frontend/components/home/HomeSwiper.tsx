"use client";

import { Children, useEffect, useRef, type ReactNode } from "react";
import type { Swiper as SwiperInstance } from "swiper";
import { EffectCreative, Keyboard, Mousewheel, Scrollbar } from "swiper/modules";
import { Swiper, SwiperSlide } from "swiper/react";

import "swiper/css";
import "swiper/css/effect-creative";
import "swiper/css/scrollbar";

const TRANSITION_MS = 700;

function respectReducedMotion(swiper: SwiperInstance) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) swiper.params.speed = 0;
}

/**
 * Lets a swipe on the last slide scroll on to the footer. Only there: touchReleaseOnEdges hands the
 * gesture to the browser, so leaving it on for every slide would stop swiping between them.
 */
function releaseTouchOnLastSlide(swiper: SwiperInstance) {
  swiper.params.touchReleaseOnEdges = swiper.isEnd;
  swiper.el.style.touchAction = swiper.isEnd ? "auto" : "";
}

/** Full-height vertical sections: the next one slides up over the current. At the end the page scrolls on to the footer. */
export function HomeSwiper({ children, withAnnouncement }: { children: ReactNode; withAnnouncement: boolean }) {
  const slides = Children.toArray(children);
  const swiperRef = useRef<SwiperInstance>(null);

  // Below the slider (at the footer) gestures belong to the page, so they scroll back up.
  useEffect(() => {
    const onScroll = () => {
      if (window.scrollY > 0) swiperRef.current?.disable();
      else swiperRef.current?.enable();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <Swiper
      modules={[EffectCreative, Keyboard, Mousewheel, Scrollbar]}
      direction="vertical"
      effect="creative"
      creativeEffect={{ prev: { shadow: true, translate: [0, "0%", -1] }, next: { translate: [0, "100%", 0] } }}
      mousewheel={{ releaseOnEdges: true }}
      keyboard={{ enabled: true }}
      scrollbar={{ draggable: true }}
      speed={TRANSITION_MS}
      onSwiper={(swiper) => {
        swiperRef.current = swiper;
      }}
      onBeforeInit={respectReducedMotion}
      onAfterInit={releaseTouchOnLastSlide}
      onSlideChange={releaseTouchOnLastSlide}
      // The screen minus the sticky header: main row + border, plus the announcement bar when it is shown
      className={withAnnouncement ? "h-[calc(100dvh-6.0625rem)]" : "h-[calc(100dvh-4.0625rem)]"}
      aria-label="بخش‌های صفحه اصلی"
    >
      {slides.map((slide, i) => (
        <SwiperSlide key={i} className="bg-paper overflow-hidden">
          {slide}
        </SwiperSlide>
      ))}
    </Swiper>
  );
}
