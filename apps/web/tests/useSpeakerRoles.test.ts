import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useSpeakerRoles } from "../src/hooks/useSpeakerRoles";

describe("useSpeakerRoles", () => {
  it("defaults every speaker label to unassigned", () => {
    const { result } = renderHook(() => useSpeakerRoles());
    expect(result.current.roleFor("speaker_a")).toBe("unassigned");
  });

  it("lets a speaker be assigned a role independently of other speakers", () => {
    const { result } = renderHook(() => useSpeakerRoles());

    act(() => result.current.assignRole("speaker_a", "doctor"));

    expect(result.current.roleFor("speaker_a")).toBe("doctor");
    expect(result.current.roleFor("speaker_b")).toBe("unassigned");
  });

  it("lets an assignment be changed later, never locking in the first guess", () => {
    const { result } = renderHook(() => useSpeakerRoles());

    act(() => result.current.assignRole("speaker_a", "doctor"));
    act(() => result.current.assignRole("speaker_a", "patient"));

    expect(result.current.roleFor("speaker_a")).toBe("patient");
  });
});
