const chartTextColor = "#d9e6f2";
const chartGridColor = "rgba(148, 163, 184, 0.18)";

const categoryCanvas = document.getElementById("categoryChart");
if (categoryCanvas) {
  new Chart(categoryCanvas, {
    type: "doughnut",
    data: {
      labels: JSON.parse(categoryCanvas.dataset.labels || "[]"),
      datasets: [{
        data: JSON.parse(categoryCanvas.dataset.values || "[]"),
        backgroundColor: ["#ff7a59","#56cfe1","#3a86ff","#ffd166","#72efdd","#f15bb5","#90be6d","#9b5de5","#f4a261","#adb5bd"],
        borderWidth: 0
      }]
    },
    options: {
      cutout: "62%",
      plugins: { legend: { labels: { color: chartTextColor } } }
    }
  });
}

const talukCanvas = document.getElementById("talukChart");
if (talukCanvas) {
  new Chart(talukCanvas, {
    type: "bar",
    data: {
      labels: JSON.parse(talukCanvas.dataset.labels || "[]"),
      datasets: [{
        data: JSON.parse(talukCanvas.dataset.values || "[]"),
        backgroundColor: ["#ff7a59","#56cfe1","#3a86ff","#ffd166","#90be6d","#9b5de5","#f15bb5","#4cc9f0"],
        borderRadius: 14
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: chartTextColor }, grid: { color: chartGridColor } },
        y: { ticks: { color: chartTextColor }, grid: { color: chartGridColor } }
      }
    }
  });
}

const placeSearch = document.getElementById("place-search");
const placeCards = [...document.querySelectorAll(".search-card")];
const placeFilters = [...document.querySelectorAll(".place-filter")];
if (placeSearch && placeCards.length) {
  let activeCategory = "All";
  const applyPlaceFilters = () => {
    const query = placeSearch.value.trim().toLowerCase();
    placeCards.forEach(card => {
      const name = card.dataset.name || "";
      const category = card.dataset.category || "";
      const matchesText = !query || name.includes(query);
      const matchesCategory = activeCategory === "All" || category === activeCategory;
      card.style.display = matchesText && matchesCategory ? "" : "none";
    });
  };
  placeSearch.addEventListener("input", applyPlaceFilters);
  placeFilters.forEach(chip => {
    chip.addEventListener("click", () => {
      activeCategory = chip.dataset.filter;
      placeFilters.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      applyPlaceFilters();
    });
  });
}

function matchesInterest(place, interest) {
  const tags = place.interest_tags || [];
  return tags.includes(interest);
}

function renderRecommendationCard(place) {
  const reasons = (place.reasons || []).map(reason => `<span class="tag">${reason}</span>`).join("");
  const companions = (place.companions || []).slice(0, 4).map(item => `<span class="tag">${item.label}</span>`).join("");
  const facilityTags = (place.facility_tags || []).slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join("");
  return `
    <article class="recommend-card">
      <div class="recommend-visual">
        ${place.photo_url ? `<img src="${place.photo_url}" alt="${place.place_name}">` : `<div class="image-fallback">${(place.theme || "T").slice(0, 1)}</div>`}
        <div class="recommend-overlay">
          <span class="rank-badge">${Math.round(place.recommendation_score || 0)}</span>
          <span class="soft-tag">${place.network_role}</span>
        </div>
      </div>
      <div class="recommend-body">
        <div class="place-top">
          <span class="tag">${place.category_label || place.category}</span>
          <span class="tag">${place.taluk}</span>
          <span class="tag">${place.theme || "Explore"}</span>
        </div>
        <h3>${place.place_name}</h3>
        <p>${place.summary || ""}</p>
        <div class="metric-inline recommend-metrics">
          <span>⭐ ${(place.rating || 0).toFixed(1)}</span>
          <span>${Math.round(place.total_user_ratings || 0)} reviews</span>
          <span>${Math.round(place.connection_count || 0)} links</span>
        </div>
        <div class="tag-cloud">${facilityTags}${reasons}</div>
        ${companions ? `<div class="network-note"><strong>Connected with:</strong><div class="tag-cloud">${companions}</div></div>` : ""}
        <div class="card-actions">
          ${place.google_maps_url ? `<a class="text-link" href="${place.google_maps_url}" target="_blank" rel="noopener">Open in Maps</a>` : ""}
          <span class="muted">Remote score ${Math.round(place.remote_score || 0)}</span>
        </div>
      </div>
    </article>
  `;
}

function renderItineraryCard(place, index) {
  return `
    <article class="itinerary-card">
      <div class="itinerary-index">${index}</div>
      ${place.photo_url ? `<img src="${place.photo_url}" alt="${place.place_name}">` : `<div class="image-fallback">${(place.theme || "T").slice(0, 1)}</div>`}
      <div class="itinerary-body">
        <h4>${place.place_name}</h4>
        <div class="place-top">
          <span class="tag">${place.category_label || place.category}</span>
          <span class="tag">${place.taluk}</span>
        </div>
        <div class="metric-inline">
          <span>⭐ ${(place.rating || 0).toFixed(1)}</span>
          <span>${Math.round(place.total_user_ratings || 0)} reviews</span>
          <span>${Math.round(place.connection_count || 0)} links</span>
        </div>
        <p class="muted">${place.formatted_address || ""}</p>
      </div>
    </article>
  `;
}

const recommendationResults = document.getElementById("recommendation-results");
if (recommendationResults) {
  const places = JSON.parse(recommendationResults.dataset.places || "[]");
  const categoryButtons = [...document.querySelectorAll(".rec-chip")];
  const interestButtons = [...document.querySelectorAll(".interest-chip")];
  const transportButtons = [...document.querySelectorAll(".transport-chip")];
  const plannerTabs = [...document.querySelectorAll(".planner-tab")];
  const plannerViews = [...document.querySelectorAll(".planner-view")];
  const talukFilter = document.getElementById("taluk-filter");
  const sortFilter = document.getElementById("sort-filter");
  const searchFilter = document.getElementById("recommendation-search");
  const distanceFilter = document.getElementById("distance-filter");
  const distanceOutput = document.getElementById("distance-output");
  const remoteToggle = document.getElementById("remote-toggle");
  const connectedToggle = document.getElementById("highly-connected-toggle");
  const recommendationTitle = document.getElementById("recommendation-title");
  const recommendationSubtitle = document.getElementById("recommendation-subtitle");
  const findButton = document.getElementById("find-recommendations");

  const itineraryView = document.getElementById("itinerary-view");
  const itineraryPlaces = itineraryView ? JSON.parse(itineraryView.dataset.places || "[]") : [];
  const durationButtons = [...document.querySelectorAll(".itinerary-chip")];
  const itineraryTalukButtons = [...document.querySelectorAll(".taluk-choice")];
  const itineraryInterestButtons = [...document.querySelectorAll(".itinerary-interest")];
  const itineraryTransportButtons = [...document.querySelectorAll(".itinerary-transport")];
  const itineraryStyle = document.getElementById("itinerary-style");
  const generateItinerary = document.getElementById("generate-itinerary");
  const itineraryTitle = document.getElementById("itinerary-title");

  let activeCategory = null;
  let activeTransport = "car";
  let itineraryTransport = "car";
  let activeDuration = "1 Day";

  plannerTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.plannerTab;
      plannerTabs.forEach(item => item.classList.toggle("active", item === tab));
      plannerViews.forEach(view => view.classList.toggle("active", view.dataset.plannerView === target));
    });
  });

  categoryButtons.forEach(button => {
    button.addEventListener("click", () => {
      const isSame = activeCategory === button.dataset.category;
      activeCategory = isSame ? null : button.dataset.category;
      categoryButtons.forEach(b => b.classList.toggle("active", !isSame && b === button));
      renderRecommendations();
    });
  });

  interestButtons.forEach(button => {
    button.addEventListener("click", () => {
      button.classList.toggle("active");
      renderRecommendations();
    });
  });

  transportButtons.forEach(button => {
    button.addEventListener("click", () => {
      activeTransport = button.dataset.transport;
      transportButtons.forEach(b => b.classList.toggle("active", b === button));
      renderRecommendations();
    });
  });

  if (distanceFilter && distanceOutput) {
    distanceFilter.addEventListener("input", () => {
      distanceOutput.textContent = `${distanceFilter.value} km`;
      renderRecommendations();
    });
  }

  const getSelectedInterests = () =>
    interestButtons.filter(button => button.classList.contains("active")).map(button => button.dataset.interest);

  function applyTransportPenalty(place) {
    const remoteScore = Number(place.remote_score || 0);
    if (activeTransport === "bike") return remoteScore <= Number(distanceFilter.value || 40) - 10;
    if (activeTransport === "bus") return remoteScore <= Number(distanceFilter.value || 40);
    return remoteScore <= Number(distanceFilter.value || 40) + 10;
  }

  function renderRecommendations() {
    const taluk = talukFilter ? talukFilter.value : "All";
    const sortBy = sortFilter ? sortFilter.value : "recommendation_score";
    const query = searchFilter ? searchFilter.value.trim().toLowerCase() : "";
    const selectedInterests = getSelectedInterests();
    let filtered = places.slice();

    if (activeCategory) filtered = filtered.filter(place => (place.category_label || place.category) === activeCategory);
    if (taluk !== "All") filtered = filtered.filter(place => place.taluk === taluk);
    if (selectedInterests.length) filtered = filtered.filter(place => selectedInterests.some(interest => matchesInterest(place, interest)));
    if (query) {
      filtered = filtered.filter(place =>
        [
          place.place_name,
          place.taluk,
          place.theme,
          place.category_label,
          place.summary,
          ...(place.interest_tags || []),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(query)
      );
    }
    if (!remoteToggle?.checked) filtered = filtered.filter(place => Number(place.remote_score || 0) <= Number(distanceFilter?.value || 40));
    filtered = filtered.filter(applyTransportPenalty);
    if (connectedToggle?.checked) filtered = filtered.filter(place => Number(place.connection_count || 0) >= 12);

    filtered = filtered
      .sort((a, b) => Number(b[sortBy] || 0) - Number(a[sortBy] || 0))
      .slice(0, 12);

    if (recommendationTitle) {
      const interestText = selectedInterests.length ? selectedInterests.join(", ") : "all themes";
      recommendationTitle.textContent = `${filtered.length} recommendations for ${interestText}`;
    }
    if (recommendationSubtitle) {
      recommendationSubtitle.textContent = taluk === "All"
        ? `Filtered using ${activeTransport} travel mode and a ${distanceFilter?.value || 40} km exploration radius.`
        : `Focused on ${taluk} with ${activeTransport} travel and graph-aware filtering.`;
    }

    if (!filtered.length) {
      recommendationResults.innerHTML = `<div class="empty-state panel"><h3>No places matched</h3><p class="muted">Try widening the radius, enabling remote gems, or clearing some interests.</p></div>`;
      return;
    }
    recommendationResults.innerHTML = filtered.map(renderRecommendationCard).join("");
  }

  [talukFilter, sortFilter, searchFilter, remoteToggle, connectedToggle].forEach(element => {
    if (!element) return;
    const eventName = element.tagName === "INPUT" && element.type === "search" ? "input" : "change";
    element.addEventListener(eventName, renderRecommendations);
  });
  if (findButton) findButton.addEventListener("click", renderRecommendations);
  renderRecommendations();

  durationButtons.forEach(button => {
    button.addEventListener("click", () => {
      activeDuration = button.dataset.duration;
      durationButtons.forEach(b => b.classList.toggle("active", b === button));
    });
  });

  itineraryTalukButtons.forEach(button => {
    button.addEventListener("click", () => button.classList.toggle("active"));
  });

  itineraryInterestButtons.forEach(button => {
    button.addEventListener("click", () => button.classList.toggle("active"));
  });

  itineraryTransportButtons.forEach(button => {
    button.addEventListener("click", () => {
      itineraryTransport = button.dataset.transport;
      itineraryTransportButtons.forEach(b => b.classList.toggle("active", b === button));
    });
  });

  function scoreItineraryPlace(place, selectedInterests, selectedTaluks, style) {
    let score = Number(place.recommendation_score || 0);
    if (selectedTaluks.includes(place.taluk)) score += 20;
    if (selectedInterests.length && selectedInterests.some(interest => matchesInterest(place, interest))) score += 22;
    if (style === "nature" && place.theme === "Nature") score += 30;
    if (style === "spiritual" && place.theme === "Spiritual") score += 30;
    if (style === "connectivity") score += Number(place.connection_count || 0) * 1.5;
    if (itineraryTransport === "bike") score -= Number(place.remote_score || 0) * 0.4;
    if (itineraryTransport === "bus") score -= Number(place.remote_score || 0) * 0.15;
    return score;
  }

  function renderCustomItinerary() {
    if (!itineraryView) return;
    const selectedTaluks = itineraryTalukButtons.filter(button => button.classList.contains("active")).map(button => button.dataset.taluk);
    const selectedInterests = itineraryInterestButtons.filter(button => button.classList.contains("active")).map(button => button.dataset.interest);
    const style = itineraryStyle ? itineraryStyle.value : "balanced";
    const desiredCount = activeDuration === "1 Day" ? 4 : activeDuration === "2 Days" ? 8 : 12;

    let pool = itineraryPlaces
      .filter(place => !selectedTaluks.length || selectedTaluks.includes(place.taluk))
      .filter(place => !selectedInterests.length || selectedInterests.some(interest => matchesInterest(place, interest)))
      .map(place => ({ ...place, _itineraryScore: scoreItineraryPlace(place, selectedInterests, selectedTaluks, style) }))
      .sort((a, b) => b._itineraryScore - a._itineraryScore);

    if (!pool.length) {
      itineraryView.innerHTML = `<div class="empty-state panel"><h3>No itinerary generated</h3><p class="muted">Select more taluks or interests to widen the itinerary pool.</p></div>`;
      return;
    }

    const picked = [];
    const used = new Set();
    const dayThemes = ["Nature", "Spiritual", "Scenic Drive", "Connector", "Explore"];

    while (picked.length < desiredCount && pool.length) {
      for (const theme of dayThemes) {
        const next = pool.find(place => !used.has(place.place_id) && (place.theme === theme || style === "balanced"));
        if (next) {
          picked.push(next);
          used.add(next.place_id);
        }
        if (picked.length >= desiredCount) break;
      }
      pool = pool.filter(place => !used.has(place.place_id));
    }

    if (picked.length < desiredCount) {
      const fallback = itineraryPlaces
        .filter(place => !used.has(place.place_id))
        .sort((a, b) => Number(b.recommendation_score || 0) - Number(a.recommendation_score || 0));
      for (const item of fallback) {
        picked.push(item);
        used.add(item.place_id);
        if (picked.length >= desiredCount) break;
      }
    }

    if (itineraryTitle) {
      itineraryTitle.textContent = `${activeDuration} itinerary for ${selectedTaluks.length ? selectedTaluks.join(", ") : "Tenkasi"}`;
    }

    const perDay = 4;
    let html = "";
    for (let i = 0; i < picked.length; i += perDay) {
      const dayItems = picked.slice(i, i + perDay);
      html += `<section class="day-lane"><div class="day-badge">Day ${i / perDay + 1}</div><div class="itinerary-grid">` +
        dayItems.map((place, idx) => renderItineraryCard(place, i + idx + 1)).join("") +
        `</div></section>`;
    }
    itineraryView.innerHTML = html;
  }

  if (generateItinerary) generateItinerary.addEventListener("click", renderCustomItinerary);
  renderCustomItinerary();
}

function setupGraph(container) {
  const payload = JSON.parse(container.dataset.graph || "{\"nodes\":[],\"links\":[]}");
  if (!payload.nodes.length) return;

  const root = container.closest(".panel, .graph-main, body") || document;
  const searchInput = document.getElementById("graph-search");
  const edgeSlider = document.getElementById("graph-edge-threshold");
  const edgeOutput = document.getElementById("graph-edge-output");
  const labelToggle = document.getElementById("graph-label-toggle");
  const resetButton = document.getElementById("graph-reset");
  const detailPanel = document.getElementById("graph-node-detail");
  const chips = [...document.querySelectorAll(".graph-color-chip")];

  const width = container.clientWidth || 1100;
  const height = container.clientHeight || 620;
  const svg = d3.select(container).append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g");
  const zoom = d3.zoom().scaleExtent([0.45, 4]).on("zoom", ({ transform }) => g.attr("transform", transform));
  svg.call(zoom);

  let mode = "community";
  let threshold = edgeSlider ? Number(edgeSlider.value) : 4;

  const colorBy = (currentMode, node) => {
    if (currentMode === "category") {
      const map = {
        "Tourist Attraction": "#ff7a59",
        "Temple": "#ffb703",
        "Park": "#72efdd",
        "Nature Spot": "#4cc9f0",
        "Museum": "#f15bb5",
        "Church": "#90be6d",
        "Mosque": "#c77dff",
      };
      return map[node.category] || "#3a86ff";
    }
    if (currentMode === "taluk") {
      const map = {
        Tenkasi: "#ff7a59",
        Shenkottai: "#4cc9f0",
        Kadayanallur: "#3a86ff",
        Sankarankovil: "#ffd166",
        Alangulam: "#90be6d",
        Sivagiri: "#c77dff",
        Veerakeralampudur: "#f15bb5",
        Thiruvengadam: "#72efdd",
      };
      return map[node.taluk] || "#94a3b8";
    }
    if (currentMode === "pagerank") {
      return d3.interpolateTurbo(Math.min(1, Number(node.pagerank || 0) * 80));
    }
    return d3.schemeTableau10[node.community % 10];
  };

  const allLinks = payload.links.map(link => ({ ...link }));
  const nodes = payload.nodes.map(node => ({ ...node }));
  const nodeById = new Map(nodes.map(node => [node.id, node]));

  const linkLayer = g.append("g");
  const nodeLayer = g.append("g");
  const labelLayer = g.append("g");

  let simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink().id(d => d.id).distance(d => 90 - Math.min(28, Number(d.weight || 1) * 4.5)).strength(0.16))
    .force("charge", d3.forceManyBody().strength(-170))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => 8 + Math.min(16, Number(d.pagerank || 0) * 180)));

  let linkSelection;
  let nodeSelection;
  let labelSelection;

  function filteredLinks() {
    const filtered = allLinks.filter(link => Number(link.weight || 1) >= threshold);
    if (filtered.length <= 220) return filtered;
    return filtered.slice().sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0)).slice(0, 220);
  }

  function render() {
    const visibleLinks = filteredLinks();
    const linkedIds = new Set();
    visibleLinks.forEach(link => {
      linkedIds.add(typeof link.source === "object" ? link.source.id : link.source);
      linkedIds.add(typeof link.target === "object" ? link.target.id : link.target);
    });

    const visibleNodes = nodes.filter(node => linkedIds.has(node.id) || !visibleLinks.length);

    linkSelection = linkLayer.selectAll("line")
      .data(visibleLinks, d => `${typeof d.source === "object" ? d.source.id : d.source}-${typeof d.target === "object" ? d.target.id : d.target}`)
      .join("line")
      .attr("stroke", "rgba(120, 141, 171, 0.24)")
      .attr("stroke-linecap", "round")
      .attr("stroke-width", d => Math.min(4, 0.45 + Number(d.weight || 1) * 0.35));

    nodeSelection = nodeLayer.selectAll("circle")
      .data(visibleNodes, d => d.id)
      .join("circle")
      .attr("r", d => 5 + Math.min(14, Number(d.pagerank || 0) * 170))
      .attr("fill", d => colorBy(mode, d))
      .attr("stroke", "#071018")
      .attr("stroke-width", 1.4)
      .attr("class", "graph-node")
      .on("click", (_, d) => showNodeDetails(d))
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    nodeSelection.append("title").text(d => d.label);

    labelSelection = labelLayer.selectAll("text")
      .data(visibleNodes, d => d.id)
      .join("text")
      .text(d => d.label.length > 18 ? `${d.label.slice(0, 18)}…` : d.label)
      .attr("font-size", 10)
      .attr("fill", "#c9d8e8")
      .style("display", labelToggle && !labelToggle.checked ? "none" : "block");

    simulation.nodes(visibleNodes);
    simulation.force("link").links(visibleLinks);
    simulation.alpha(0.65).restart();
    simulation.on("tick", () => {
      linkSelection
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      nodeSelection
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
      labelSelection
        .attr("x", d => d.x + 10)
        .attr("y", d => d.y + 4);
    });
  }

  function showNodeDetails(node) {
    if (!detailPanel) return;
    detailPanel.innerHTML = `
      ${node.photo_url ? `<img src="${node.photo_url}" alt="${node.label}">` : ""}
      <h4>${node.label}</h4>
      <div class="tag-cloud">
        <span class="tag">${node.category}</span>
        <span class="tag">${node.taluk}</span>
        <span class="tag">${node.network_role || "Network Participant"}</span>
      </div>
      <div class="metric-inline">
        <span>PageRank ${(Number(node.pagerank || 0)).toFixed(4)}</span>
        <span>Degree ${(Number(node.degree || 0)).toFixed(4)}</span>
        <span>Community ${node.community || 0}</span>
      </div>
    `;
    nodeSelection.attr("stroke", d => d.id === node.id ? "#ffd166" : "#071018").attr("stroke-width", d => d.id === node.id ? 3 : 1.4);
  }

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      mode = chip.dataset.mode;
      chips.forEach(item => item.classList.toggle("active", item === chip));
      if (nodeSelection) nodeSelection.attr("fill", d => colorBy(mode, d));
    });
  });

  if (edgeSlider) {
    edgeSlider.addEventListener("input", () => {
      threshold = Number(edgeSlider.value);
      if (edgeOutput) edgeOutput.textContent = threshold.toFixed(1);
      render();
    });
  }

  if (labelToggle) {
    labelToggle.addEventListener("change", () => {
      if (labelSelection) labelSelection.style("display", labelToggle.checked ? "block" : "none");
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.trim().toLowerCase();
      if (!nodeSelection) return;
      nodeSelection
        .attr("opacity", d => !query || d.label.toLowerCase().includes(query) ? 1 : 0.18)
        .attr("stroke", d => query && d.label.toLowerCase().includes(query) ? "#ffd166" : "#071018")
        .attr("stroke-width", d => query && d.label.toLowerCase().includes(query) ? 3 : 1.4);
      if (labelSelection) labelSelection.attr("opacity", d => !query || d.label.toLowerCase().includes(query) ? 1 : 0.2);
    });
  }

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
      simulation.alpha(1).restart();
    });
  }

  render();
}

document.querySelectorAll("#graph-view").forEach(setupGraph);
