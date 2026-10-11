import { describe, expect, it } from "vitest";
import { parseCitations } from "./api";

describe("parseCitations", () => {
  it("splits text and citation markers", () => {
    expect(parseCitations("Use prepared statements [1] and checks [2][3].")).toEqual([
      "Use prepared statements ",
      1,
      " and checks ",
      2,
      3,
      ".",
    ]);
  });

  it("returns plain text unchanged", () => {
    expect(parseCitations("No citations here")).toEqual(["No citations here"]);
  });
});
