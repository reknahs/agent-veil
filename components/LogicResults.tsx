import React from "react";

type ErrorItem = {
    title: string;
    issueSummary: string;
    description: string;
    status: string;
    pullRequestUrl?: string;
};

type ScanResult = {
    ok: boolean;
    summary: string;
    message: string;
    errors?: ErrorItem[];
};

type CardState = "Error" | "In progress" | "Completed";

function getCardKey(index: number, err: ErrorItem): string {
    const title = (err?.title ?? "").slice(0, 50);
    const summary = (err?.issueSummary ?? "").slice(0, 30);
    return `finding-${index}-${title}-${summary}`;
}

function getCardState(
    err: ErrorItem,
    cardKey: string,
    inProgressKeys: Set<string>
): CardState {
    if (err?.pullRequestUrl) return "Completed";
    if (inProgressKeys.has(cardKey)) return "In progress";
    return "Error";
}

interface LogicResultsProps {
    loading: boolean;
    result: ScanResult | null;
    streamingErrors: ErrorItem[];
    inProgressSet: Set<string>;
    onSelectError: (err: ErrorItem, key: string) => void;
}

export default function LogicResults({
    loading,
    result,
    streamingErrors,
    inProgressSet,
    onSelectError,
}: LogicResultsProps) {
    return (
        <section className="findings-section">
            <header className="findings-header">
                <h2 className="findings-title">Logic Findings</h2>
                {loading && streamingErrors.length === 0 && !result && (
                    <span className="findings-badge findings-badge-loading">Analyzing…</span>
                )}
                {result?.message && !loading && (
                    <span className="findings-count">{result.message}</span>
                )}
                {loading && streamingErrors.length > 0 && (
                    <span className="findings-count">{streamingErrors.length} issue(s) so far…</span>
                )}
            </header>

            {!result?.errors?.length && !streamingErrors.length && result?.ok && !loading && (
                <div className="finding-card finding-card-empty">
                    <p>No issues found.</p>
                </div>
            )}

            {((result?.errors?.length ?? 0) > 0 || streamingErrors.length > 0) && (
                <div className="finding-cards-grid" role="list">
                    {(loading ? streamingErrors : result?.errors ?? []).map((err, i) => {
                        const cardKey = getCardKey(i, err);
                        const state = getCardState(err, cardKey, inProgressSet);
                        const safeTitle = err?.title ?? "Issue";
                        const safeSummary = err?.issueSummary ?? "";
                        return (
                            <button
                                key={cardKey}
                                type="button"
                                className="finding-card"
                                onClick={() => onSelectError(err, cardKey)}
                                role="listitem"
                            >
                                <span className={`finding-card-state finding-card-state-${state.replace(/\s+/g, "-").toLowerCase()}`}>
                                    {state}
                                </span>
                                <h3 className="finding-card-title">{safeTitle}</h3>
                                <p className="finding-card-description">{safeSummary || "Agent reported failure or bug."}</p>
                            </button>
                        );
                    })}
                </div>
            )}

            {result && !result.ok && ((result?.errors?.length ?? 0) === 0 && !streamingErrors.length) && (
                <div className="finding-card finding-card-error" role="alert">
                    <p>{result.message ?? "Something went wrong."}</p>
                </div>
            )}
        </section>
    );
}
