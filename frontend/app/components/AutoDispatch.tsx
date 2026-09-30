"use client";

import React from "react";

export default function AutoDispatch() {
  const dispatchStarted = React.useRef(false);

  React.useEffect(() => {
    if (dispatchStarted.current) return;

    dispatchStarted.current = true;

    async function dispatchWarning() {
      try {
        const API_BASE_URL =
          process.env.NEXT_PUBLIC_API_BASE_URL ||
          "http://127.0.0.1:8000";

        const response = await fetch(
          `${API_BASE_URL}/api/cyclones/CY001/dispatch?hours=36`,
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Dispatch failed with status ${response.status}`
          );
        }

        const result = await response.json();

        console.log(
          "Automatic warning dispatch successful:",
          result
        );

        window.alert(
          "Warning Dispatched\n\nAutomatic mail and SMS notifications have been sent successfully."
        );
      } catch (error) {
        console.error(
          "Automatic warning dispatch failed:",
          error
        );
      }
    }

    dispatchWarning();
  }, []);

  return null;
}
