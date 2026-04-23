import json
import time
from agent.orchestrator import run_full_flow

# 20 synthetic prospects
prospects = [
    {
        "company": "DataFlow Inc",
        "email": "cto@dataflow.io",
        "name": "Sarah Chen",
        "domain": "dataflow.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 5,
                "total_open_roles": 15,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "CloudScale",
        "email": "vpe@cloudscale.io",
        "name": "James Wilson",
        "domain": "cloudscale.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 1,
                "total_open_roles": 20,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": True,
                "role": "cto",
                "new_leader_name": "James Wilson",
                "started_at": "2026-02-15",
                "source_url": "https://cloudscale.io/blog"
            }
        }
    },
    {
        "company": "MLOps Co",
        "email": "founder@mlops.co",
        "name": "Priya Patel",
        "domain": "mlops.co",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 4,
                "total_open_roles": 8,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "FintechRapid",
        "email": "cto@fintechrapid.com",
        "name": "David Kim",
        "domain": "fintechrapid.com",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 0,
                "total_open_roles": 5,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": False,
                "modern_ml_stack": False,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "AIStartup Labs",
        "email": "ceo@aistartup.ai",
        "name": "Maya Johnson",
        "domain": "aistartup.ai",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 6,
                "total_open_roles": 12,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "DevOps Pro",
        "email": "vpe@devopspro.com",
        "name": "Tom Anderson",
        "domain": "devopspro.com",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 2,
                "total_open_roles": 18,
                "has_ai_leadership": False,
                "github_ai_activity": True,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": True,
                "role": "vp_engineering",
                "new_leader_name": "Tom Anderson",
                "started_at": "2026-03-01",
                "source_url": "https://linkedin.com"
            }
        }
    },
    {
        "company": "DataBridge",
        "email": "cto@databridge.io",
        "name": "Lisa Zhang",
        "domain": "databridge.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 3,
                "total_open_roles": 9,
                "has_ai_leadership": True,
                "github_ai_activity": False,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "ScaleAI Corp",
        "email": "founder@scaleai.co",
        "name": "Ahmed Hassan",
        "domain": "scaleai.co",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 7,
                "total_open_roles": 14,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "CloudNative Inc",
        "email": "cto@cloudnative.io",
        "name": "Emma Davis",
        "domain": "cloudnative.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 0,
                "total_open_roles": 8,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": False,
                "modern_ml_stack": False,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "PlatformX",
        "email": "vpe@platformx.com",
        "name": "Robert Lee",
        "domain": "platformx.com",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 2,
                "total_open_roles": 25,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": True,
                "modern_ml_stack": False,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "TechVentures",
        "email": "ceo@techventures.io",
        "name": "Nina Patel",
        "domain": "techventures.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 4,
                "total_open_roles": 10,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "Inframatic",
        "email": "cto@inframatic.dev",
        "name": "Chris Brown",
        "domain": "inframatic.dev",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 1,
                "total_open_roles": 12,
                "has_ai_leadership": False,
                "github_ai_activity": True,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": True,
                "role": "cto",
                "new_leader_name": "Chris Brown",
                "started_at": "2026-01-20",
                "source_url": "https://inframatic.dev"
            }
        }
    },
    {
        "company": "ModelHub",
        "email": "founder@modelhub.ai",
        "name": "Zara Ali",
        "domain": "modelhub.ai",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 5,
                "total_open_roles": 7,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "DataMesh Co",
        "email": "cto@datamesh.co",
        "name": "Frank Miller",
        "domain": "datamesh.co",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 3,
                "total_open_roles": 11,
                "has_ai_leadership": True,
                "github_ai_activity": False,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "BuildFast",
        "email": "vpe@buildfast.dev",
        "name": "Sophie Turner",
        "domain": "buildfast.dev",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 0,
                "total_open_roles": 6,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": False,
                "modern_ml_stack": False,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "RestructureTech",
        "email": "cfo@restructuretech.com",
        "name": "Mark Davis",
        "domain": "restructuretech.com",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 2,
                "total_open_roles": 8,
                "has_ai_leadership": False,
                "github_ai_activity": False,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "AgentFlow",
        "email": "ceo@agentflow.ai",
        "name": "Yuki Tanaka",
        "domain": "agentflow.ai",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 6,
                "total_open_roles": 10,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "StreamData",
        "email": "cto@streamdata.io",
        "name": "Carlos Rodriguez",
        "domain": "streamdata.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 2,
                "total_open_roles": 13,
                "has_ai_leadership": False,
                "github_ai_activity": True,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "NexusAI",
        "email": "founder@nexusai.io",
        "name": "Aisha Mohammed",
        "domain": "nexusai.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 4,
                "total_open_roles": 9,
                "has_ai_leadership": True,
                "github_ai_activity": False,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    },
    {
        "company": "PipelineIO",
        "email": "vpe@pipeline.io",
        "name": "Ben Taylor",
        "domain": "pipeline.io",
        "mock_signals": {
            "ai_signals": {
                "ai_open_roles": 3,
                "total_open_roles": 10,
                "has_ai_leadership": True,
                "github_ai_activity": True,
                "executive_ai_commentary": False,
                "modern_ml_stack": True,
                "strategic_ai_comms": True
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    }
]

# Run all 20 prospects
latencies = []
results = []

print(f"Running {len(prospects)} prospects...\n")

for i, prospect in enumerate(prospects, 1):
    print(f"\n--- Prospect {i}/{len(prospects)}: "
          f"{prospect['company']} ---")
    start = time.time()

    result = run_full_flow(
        company_name=prospect["company"],
        prospect_email=prospect["email"],
        prospect_name=prospect["name"],
        domain=prospect["domain"],
        mock_signals=prospect["mock_signals"],
        dry_run=True
    )

    elapsed = time.time() - start
    latencies.append(elapsed)
    results.append({
        "company": prospect["company"],
        "segment": result["steps"].get(
            "enrichment", {}
        ).get("segment", "unknown"),
        "tone_score": result["steps"].get(
            "email_composition", {}
        ).get("tone_score", 0),
        "hubspot_status": result["steps"].get(
            "hubspot", {}
        ).get("status", "unknown"),
        "latency_seconds": round(elapsed, 2),
        "status": result["status"]
    })

    print(f"  Latency: {elapsed:.2f}s")

# Calculate latency stats
latencies.sort()
p50 = latencies[len(latencies) // 2]
p95 = latencies[int(len(latencies) * 0.95)]

print(f"\n{'='*50}")
print(f"BATCH RESULTS — {len(prospects)} prospects")
print(f"{'='*50}")
print(f"p50 latency: {p50:.2f}s")
print(f"p95 latency: {p95:.2f}s")
print(f"Min latency: {min(latencies):.2f}s")
print(f"Max latency: {max(latencies):.2f}s")

# Segment distribution
segments = {}
for r in results:
    seg = r["segment"]
    segments[seg] = segments.get(seg, 0) + 1

print(f"\nSegment distribution:")
for seg, count in segments.items():
    print(f"  {seg}: {count}")

# Tone scores
avg_tone = sum(
    r["tone_score"] for r in results
) / len(results)
print(f"\nAverage tone score: {avg_tone:.1f}/5")

# Save results
import json
with open(
    "outputs/batch_results.json", "w"
) as f:
    json.dump({
        "total_prospects": len(prospects),
        "p50_latency": p50,
        "p95_latency": p95,
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "segment_distribution": segments,
        "average_tone_score": avg_tone,
        "results": results
    }, f, indent=2)

print(f"\nResults saved to outputs/batch_results.json")