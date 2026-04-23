"use client";

import { Chessboard } from "react-chessboard";
import { useMemo } from "react";

interface MiniBoardProps {
  fen: string;
  size?: number;
  highlightSquares?: string[]; // e.g. ["e4", "f6"]
  /** Whether to flip the board so Black is on the bottom. */
  blackBottom?: boolean;
}

export function MiniBoard({ fen, size = 220, highlightSquares = [], blackBottom = false }: MiniBoardProps) {
  const customSquareStyles = useMemo(() => {
    const map: Record<string, React.CSSProperties> = {};
    for (const sq of highlightSquares) {
      map[sq] = {
        background: "radial-gradient(circle, hsl(40 90% 70% / 0.5) 30%, transparent 70%)",
      };
    }
    return map;
  }, [highlightSquares]);

  return (
    <div style={{ width: size, height: size }} className="overflow-hidden rounded-md shadow">
      <Chessboard
        id={`mini-${fen.slice(0, 12)}`}
        position={fen}
        boardWidth={size}
        arePiecesDraggable={false}
        boardOrientation={blackBottom ? "black" : "white"}
        customDarkSquareStyle={{ backgroundColor: "hsl(28 35% 38%)" }}
        customLightSquareStyle={{ backgroundColor: "hsl(40 30% 92%)" }}
        customSquareStyles={customSquareStyles}
      />
    </div>
  );
}
