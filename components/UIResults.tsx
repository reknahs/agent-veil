import React from "react";

type UIResultItem = {
    status: "info" | "bug" | "done" | "error";
    message?: string;
    content?: string;
    pullRequestUrl?: string;
};

// We reuse the ErrorItem type from the parent or define a local compatible one
type ErrorItem = {
    title: string;
    issueSummary: string;
    description: string;
    status: string;
    pullRequestUrl?: string;
};

interface UIResultsProps {
    loading: boolean;
    findings: UIResultItem[];
    inProgressSet: Set<string>;
    onSelectError: (err: ErrorItem, key: string) => void;
}

export default function UIResults({ loading, findings, inProgressSet, onSelectError }: UIResultsProps) {
    // Extract only bugs for the main display grid, and keep info/status for a progress line
    const rawBugs = findings.filter(f => f.status === "bug");

    // Deduplicate and clean up
    const uniqueBugs: UIResultItem[] = [];
    const seenContent = new Set<string>();

    for (const bug of rawBugs) {
        if (!bug.content) continue;

        // Strip "Bug #\d+: " prefix for comparison and display
        const cleanContent = bug.content.replace(/^Bug #\d+:\s*/, "").trim();

        if (!seenContent.has(cleanContent)) {
            seenContent.add(cleanContent);
            uniqueBugs.push({ ...bug, content: cleanContent });
        }
    }

    const latestInfo = findings.filter(f => f.status === "info").pop()?.message;
    const error = findings.find(f => f.status === "error")?.message;

    return (
        <section className="findings-section">
            <header className="findings-header">
                <h2 className="findings-title">UI/UX Errors</h2>
                {loading && !error && (
                    <span className="findings-badge findings-badge-loading">
                        {latestInfo || "Analyzing UI/UX…"}
                    </span>
                )}
                {error && <span className="findings-count text-red-400">{error}</span>}
                {!loading && !error && (
                    <span className="findings-count">Found {uniqueBugs.length} UI/UX error(s).</span>
                )}
            </header>

            {uniqueBugs.length === 0 && !loading && !error && (
                <div className="finding-card finding-card-empty">
                    <p>No UI/UX errors found.</p>
                </div>
            )}

            {uniqueBugs.length > 0 && (
                <div className="finding-cards-grid" role="list">
                    {uniqueBugs.map((bug, i) => {
                        const lines = bug.content?.split("\n") || [];
                        const title = lines[0] || "UI Error";
                        const detail = lines.slice(1).join("\n").replace(/^Detail: /, "");

                        const errorObj: ErrorItem = {
                            title,
                            issueSummary: detail || title, // Keep the full detail as requested
                            description: bug.content || "",
                            status: "ui-error",
                            pullRequestUrl: bug.pullRequestUrl,
                        };
                        const cardKey = `ui-error-${i}`;
                        const state = bug.pullRequestUrl ? "Completed" : (inProgressSet.has(cardKey) ? "In progress" : "Error");

                        return (
                            <button
                                key={`ui-error-${i}`}
                                type="button"
                                className="finding-card"
                                onClick={() => onSelectError(errorObj, `ui-error-${i}`)}
                                role="listitem"
                            >
                                <span className={`finding-card-state finding-card-state-${state.replace(/\s+/g, "-").toLowerCase()}`}>
                                    {state.toUpperCase()}
                                </span>
                                <h3 className="finding-card-title">{title}</h3>
                                <p className="finding-card-description line-clamp-3">{detail || title}</p>
                            </button>
                        );
                    })}
                </div>
            )}

            {error && uniqueBugs.length === 0 && (
                <div className="finding-card finding-card-error" role="alert">
                    <p>{error}</p>
                </div>
            )}
        </section>
    );
}
