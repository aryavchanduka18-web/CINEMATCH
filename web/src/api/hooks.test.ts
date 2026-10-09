import { patchFilm } from "./hooks";

const card = (id: number) => ({ movie: { id, title: `F${id}` }, user_state: { rating: null, reaction: 0, in_list: false, watched: false } });

test("a like shows on every card of that film at once", () => {
  const home = { hero: [card(1), card(2)], rails: [{ key: "x", items: [card(1)] }] };
  const out = patchFilm(home, 1, { reaction: 1 }, false) as typeof home;
  expect(out.hero[0].user_state.reaction).toBe(1);
  expect(out.rails[0].items[0].user_state.reaction).toBe(1);
  expect(out.hero[1].user_state.reaction).toBe(0);
});

test("a disliked film leaves the lists straight away", () => {
  const home = { hero: [card(1), card(2)], rails: [{ key: "x", items: [card(1), card(3)] }] };
  const out = patchFilm(home, 1, { reaction: -1 }, true) as typeof home;
  expect(out.hero.map((c) => c.movie.id)).toEqual([2]);
  expect(out.rails[0].items.map((c) => c.movie.id)).toEqual([3]);
});

test("the film page record gets the new state too", () => {
  const detail = { id: 5, title: "F5", user_state: { rating: null, reaction: 0, in_list: false, watched: false } };
  expect((patchFilm(detail, 5, { in_list: true }, false) as typeof detail).user_state.in_list).toBe(true);
});
