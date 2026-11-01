export const lessons = [
  { lesson: 62, title: 'After the fire' },
  { lesson: 63, title: 'She was not amused' },
];

const storageKey = 'read-alone.lesson.v1';

export function readSelectedLesson() {
  try {
    const selected = Number(localStorage.getItem(storageKey));
    if (lessons.some(item => item.lesson === selected)) return selected;
  } catch { /* The latest course remains available without browser storage. */ }
  return lessons.at(-1).lesson;
}

export function saveSelectedLesson(lesson) {
  try { localStorage.setItem(storageKey, String(lesson)); } catch { /* Selection still works. */ }
}
