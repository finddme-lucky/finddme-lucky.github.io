import { test } from "node:test";
import assert from "node:assert/strict";
import { bucketLabel } from "../../web/js/chart.mjs";

test("합쳐진 구간은 양 끝만 남긴다", () => {
  assert.equal(bucketLabel("63~64~65~66~67~68"), "63~68");
  assert.equal(bucketLabel("12"), "12");
  assert.equal(bucketLabel(7), "7");
});
