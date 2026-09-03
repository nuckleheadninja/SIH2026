/**
 * OCR Extractor & Detection Testing Workbench Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const fileInput = document.getElementById("fileInput");
  const dropzone = document.getElementById("dropzone");
  const btnSample = document.getElementById("btnSample");
  const loader = document.getElementById("loader");
  const resultsSection = document.getElementById("resultsSection");

  const mainImage = document.getElementById("mainImage");
  const svgOverlay = document.getElementById("svgOverlay");
  const gridOverlay = document.getElementById("gridOverlay");
  const resolutionText = document.getElementById("resolutionText");

  const chkShowOverlay = document.getElementById("chkShowOverlay");
  const chkShowGrid = document.getElementById("chkShowGrid");
  const chkShowLabels = document.getElementById("chkShowLabels");

  const btnAnnotated = document.getElementById("btnAnnotated");
  const btnOriginal = document.getElementById("btnOriginal");
  const btnPreprocessed = document.getElementById("btnPreprocessed");

  const telemetryEngine = document.getElementById("telemetryEngine");
  const telemetryBlocks = document.getElementById("telemetryBlocks");
  const telemetryAvgConf = document.getElementById("telemetryAvgConf");
  const telemetryQuality = document.getElementById("telemetryQuality");

  const qualityBanner = document.getElementById("qualityBanner");
  const qualityStatusBadge = document.getElementById("qualityStatusBadge");
  const qualitySummaryText = document.getElementById("qualitySummaryText");
  const qualityWarningsList = document.getElementById("qualityWarningsList");

  const metricTotal = document.getElementById("metricTotal");
  const metricHigh = document.getElementById("metricHigh");
  const metricMed = document.getElementById("metricMed");
  const metricLow = document.getElementById("metricLow");

  const txtSearchText = document.getElementById("txtSearchText");
  const filterPills = document.querySelectorAll(".filter-pill");
  const selectRegionFilter = document.getElementById("selectRegionFilter");

  const ocrCountBadge = document.getElementById("ocrCountBadge");
  const ocrTableBody = document.getElementById("ocrTableBody");
  const spatialChipsContainer = document.getElementById("spatialChipsContainer");

  const valBlur = document.getElementById("valBlur");
  const valBrightness = document.getElementById("valBrightness");
  const valContrast = document.getElementById("valContrast");
  const valProfile = document.getElementById("valProfile");
  const valOps = document.getElementById("valOps");

  const jsonViewer = document.getElementById("jsonViewer");
  const btnCopyJson = document.getElementById("btnCopyJson");
  const btnDownloadJson = document.getElementById("btnDownloadJson");

  // State
  let currentData = null;
  let currentArtifacts = {};
  let currentBlocks = [];
  let activeConfidenceFilter = "all";
  let activeRegionFilter = "all";
  let searchQuery = "";

  const btnSelectFile = document.getElementById("btnSelectFile");
  const uploadSubText = document.getElementById("uploadSubText");

  // --- Drag and Drop & File Browsing Handlers ---
  dropzone.addEventListener("click", (e) => {
    // Only trigger if click was not on the sample button
    if (e.target !== btnSample && !btnSample.contains(e.target)) {
      fileInput.click();
    }
  });

  if (btnSelectFile) {
    btnSelectFile.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (uploadSubText) uploadSubText.textContent = `Processing: ${file.name} (${Math.round(file.size / 1024)} KB)`;
      uploadFile(file);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      if (uploadSubText) uploadSubText.textContent = `Processing: ${file.name} (${Math.round(file.size / 1024)} KB)`;
      uploadFile(file);
    }
  });

  btnSample.addEventListener("click", (e) => {
    e.stopPropagation();
    fetchSample();
  });

  // --- Image View Switcher ---
  const viewBtns = [btnAnnotated, btnOriginal, btnPreprocessed];
  viewBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      viewBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const viewMode = btn.getAttribute("data-view");

      if (viewMode === "annotated" && currentArtifacts.annotated_image_url) {
        mainImage.src = currentArtifacts.annotated_image_url + "?t=" + new Date().getTime();
        svgOverlay.style.display = chkShowOverlay.checked ? "block" : "none";
      } else if (viewMode === "original" && currentArtifacts.original_image_url) {
        mainImage.src = currentArtifacts.original_image_url + "?t=" + new Date().getTime();
      } else if (viewMode === "preprocessed" && currentArtifacts.preprocessed_image_url) {
        mainImage.src = currentArtifacts.preprocessed_image_url + "?t=" + new Date().getTime();
      }
    });
  });

  // --- Toggles ---
  chkShowOverlay.addEventListener("change", (e) => {
    svgOverlay.style.display = e.target.checked ? "block" : "none";
  });

  chkShowGrid.addEventListener("change", (e) => {
    if (e.target.checked) gridOverlay.classList.add("visible");
    else gridOverlay.classList.remove("visible");
  });

  chkShowLabels.addEventListener("change", () => {
    renderSvgOverlay();
  });

  // --- Tab Switcher ---
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((tc) => tc.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // --- Search & Filter Handlers ---
  txtSearchText.addEventListener("input", (e) => {
    searchQuery = e.target.value.trim().toLowerCase();
    applyFilters();
  });

  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      activeConfidenceFilter = pill.getAttribute("data-filter");
      applyFilters();
    });
  });

  selectRegionFilter.addEventListener("change", (e) => {
    activeRegionFilter = e.target.value;
    applyFilters();
  });

  // --- Copy JSON ---
  btnCopyJson.addEventListener("click", () => {
    if (currentData) {
      navigator.clipboard.writeText(JSON.stringify(currentData, null, 2));
      btnCopyJson.textContent = "Copied!";
      setTimeout(() => (btnCopyJson.textContent = "Copy JSON"), 2000);
    }
  });

  // --- API Handlers ---
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    showLoader(true);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });
      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseErr) {
        throw new Error(`Server response error (Status ${response.status}): ${responseText.substring(0, 200)}`);
      }
      renderDashboard(data);
    } catch (err) {
      alert("Error executing OCR Extractor: " + err.message);
    } finally {
      showLoader(false);
    }
  }

  async function fetchSample() {
    showLoader(true);
    try {
      const response = await fetch("/api/sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sample: "product_001.jpg" }),
      });
      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseErr) {
        throw new Error(`Server response error (Status ${response.status}): ${responseText.substring(0, 200)}`);
      }
      renderDashboard(data);
    } catch (err) {
      alert("Error running sample image: " + err.message);
    } finally {
      showLoader(false);
    }
  }

  function showLoader(visible) {
    if (visible) loader.classList.remove("hidden");
    else loader.classList.add("hidden");
  }

  // --- Render Dashboard UI ---
  function renderDashboard(data) {
    if (data.status !== "success") {
      alert("OCR Detection Failed: " + (data.message || data.error_code));
      return;
    }

    currentData = data;
    currentArtifacts = data.artifacts || {};
    currentBlocks = data.ocr_blocks || [];

    // 1. Reveal results panel
    resultsSection.classList.remove("hidden");

    // 2. Set image view
    btnAnnotated.classList.add("active");
    btnOriginal.classList.remove("active");
    btnPreprocessed.classList.remove("active");
    mainImage.src = currentArtifacts.annotated_image_url + "?t=" + new Date().getTime();
    resolutionText.textContent = `${data.image.width} x ${data.image.height} px`;

    // 3. Render Header Telemetry
    telemetryEngine.textContent = `${data.ocr_engine.name} (${data.ocr_engine.device.toUpperCase()})`;
    telemetryBlocks.textContent = `${currentBlocks.length} blocks`;

    const avgConf =
      currentBlocks.length > 0
        ? Math.round((currentBlocks.reduce((acc, b) => acc + b.confidence, 0) / currentBlocks.length) * 100)
        : 0;
    telemetryAvgConf.textContent = `${avgConf}%`;

    const qStatus = data.quality.quality_status;
    telemetryQuality.textContent = qStatus.toUpperCase();
    telemetryQuality.className = "badge " + (qStatus === "acceptable" ? "badge-success" : "badge-warning");

    // Quality Banner Alert
    if (data.quality.warnings && data.quality.warnings.length > 0) {
      qualityBanner.classList.remove("hidden");
      qualityStatusBadge.textContent = qStatus.toUpperCase();
      qualityStatusBadge.className = "badge " + (qStatus === "acceptable" ? "badge-success" : "badge-warning");
      qualitySummaryText.textContent = `Quality Inspection Warning(s) Detected:`;
      qualityWarningsList.innerHTML = data.quality.warnings
        .map((w) => `<span class="badge badge-warning">${w}</span>`)
        .join("");
    } else {
      qualityBanner.classList.add("hidden");
    }

    // 4. Update Summary Metric Cards
    metricTotal.textContent = currentBlocks.length;
    metricHigh.textContent = currentBlocks.filter((b) => b.confidence >= 0.90).length;
    metricMed.textContent = currentBlocks.filter((b) => b.confidence >= 0.70 && b.confidence < 0.90).length;
    metricLow.textContent = currentBlocks.filter((b) => b.confidence < 0.70).length;

    // 5. Render Quality Tab
    valBlur.textContent = data.quality.blur_score;
    valBrightness.textContent = data.quality.brightness;
    valContrast.textContent = data.quality.contrast;
    valProfile.textContent = (data.preprocessing.profile || "default").toUpperCase();
    valOps.textContent = "Applied ops: " + (data.preprocessing.operations.join(", ") || "none");

    // 5b. Render Extracted Product Fields Card Grid
    const fieldsCardGrid = document.getElementById("fieldsCardGrid");
    if (fieldsCardGrid) {
      const extracted = data.extracted_fields || {};
      const fieldKeys = [
        { key: "brand_title", label: "🏷️ Brand Title / Product Name" },
        { key: "mrp", label: "💰 Maximum Retail Price (MRP)" },
        { key: "net_quantity", label: "⚖️ Net Quantity" },
        { key: "mfg_date", label: "📅 Mfg Date / Packed Date" },
        { key: "expiry_date", label: "⏳ Expiry / Best Before" },
        { key: "batch_number", label: "🔢 Batch / Lot Number" },
        { key: "fssai_lic_no", label: "🛡️ FSSAI License Number" },
      ];

      fieldsCardGrid.innerHTML = fieldKeys.map(f => {
        const item = extracted[f.key] || {};
        const val = item.value || "Not Detected";
        const isFound = Boolean(item.value);
        return `
          <div class="field-item-card">
            <div class="field-label">${f.label}</div>
            <div class="field-val-box" style="color: ${isFound ? '#10b981' : '#64748b'}">${val}</div>
            ${item.evidence_block_id ? `<div class="field-evidence-sub">Evidence Block: <code>${item.evidence_block_id}</code></div>` : '<div class="field-evidence-sub">Not found in OCR blocks</div>'}
          </div>
        `;
      }).join("");
    }

    // 6. Render Spatial Relations
    const relations = data.spatial_relations || [];
    if (relations.length === 0) {
      spatialChipsContainer.innerHTML = '<p class="muted-text">No pairwise spatial relations computed.</p>';
    } else {
      spatialChipsContainer.innerHTML = relations
        .map(
          (r) => `
            <div class="relation-chip">
              <span class="chip-source">${r.source}</span>
              <span class="chip-rel">${r.relation}</span>
              <span class="chip-target">${r.target}</span>
              <span class="muted-text">(${Math.round(r.distance_px)}px)</span>
            </div>
          `
        )
        .join("");
    }

    // 7. Render JSON Payload
    jsonViewer.textContent = JSON.stringify(data, null, 2);
    btnDownloadJson.href = currentArtifacts.json_url;

    // 8. On image load, initialize SVG Bounding Box Overlay and Table
    mainImage.onload = () => {
      renderSvgOverlay();
      applyFilters();
    };
    // Fallback if image cached
    if (mainImage.complete) {
      renderSvgOverlay();
      applyFilters();
    }
  }

  // --- Render Interactive SVG Bounding Box Overlay ---
  function renderSvgOverlay() {
    if (!currentData || !currentBlocks.length) return;

    const imgWidth = currentData.image.width;
    const imgHeight = currentData.image.height;
    const showLabels = chkShowLabels.checked;

    svgOverlay.setAttribute("viewBox", `0 0 ${imgWidth} ${imgHeight}`);
    svgOverlay.innerHTML = "";

    currentBlocks.forEach((block) => {
      const bbox = block.bbox; // [x1, y1, x2, y2]
      const x = bbox[0];
      const y = bbox[1];
      const width = bbox[2] - bbox[0];
      const height = bbox[3] - bbox[1];

      const confLevel = block.confidence_level; // high, medium, low
      const confClass = confLevel === "high" ? "high-conf" : confLevel === "medium" ? "medium-conf" : "low-conf";

      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", `bbox-group ${confClass}`);
      group.setAttribute("data-id", block.id);

      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", x);
      rect.setAttribute("y", y);
      rect.setAttribute("width", width);
      rect.setAttribute("height", height);
      rect.setAttribute("class", `bbox-rect ${confClass}`);

      group.appendChild(rect);

      if (showLabels) {
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", x + 4);
        text.setAttribute("y", Math.max(16, y - 4));
        text.setAttribute("class", "bbox-tag");
        text.textContent = `${block.id} (${Math.round(block.confidence * 100)}%)`;
        group.appendChild(text);
      }

      // Hover Event Listeners (Two-Way Sync)
      group.addEventListener("mouseenter", () => highlightBlock(block.id));
      group.addEventListener("mouseleave", () => unhighlightBlock(block.id));

      svgOverlay.appendChild(group);
    });
  }

  // --- Apply Filters to OCR Table ---
  function applyFilters() {
    if (!currentBlocks) return;

    const filtered = currentBlocks.filter((b) => {
      // 1. Text Search Filter
      const textMatch =
        !searchQuery ||
        b.raw_text.toLowerCase().includes(searchQuery) ||
        b.normalized_text.toLowerCase().includes(searchQuery) ||
        b.id.toLowerCase().includes(searchQuery);

      // 2. Confidence Filter
      const confMatch =
        activeConfidenceFilter === "all" ||
        (activeConfidenceFilter === "high" && b.confidence >= 0.90) ||
        (activeConfidenceFilter === "medium" && b.confidence >= 0.70 && b.confidence < 0.90) ||
        (activeConfidenceFilter === "low" && b.confidence < 0.70);

      // 3. Region Filter
      const regionMatch = activeRegionFilter === "all" || b.layout.region === activeRegionFilter;

      return textMatch && confMatch && regionMatch;
    });

    ocrCountBadge.textContent = filtered.length;

    ocrTableBody.innerHTML = filtered
      .map((b) => {
        const confBadge =
          b.confidence_level === "high"
            ? "badge-success"
            : b.confidence_level === "medium"
            ? "badge-warning"
            : "badge-error";
        const confPct = Math.round(b.confidence * 100);

        return `
          <tr id="row_${b.id}" data-id="${b.id}">
            <td><strong>#${b.reading_order}</strong></td>
            <td><code>${b.id}</code></td>
            <td><code>${escapeHtml(b.raw_text)}</code></td>
            <td><strong>${escapeHtml(b.normalized_text)}</strong></td>
            <td><span class="badge ${confBadge}">${confPct}%</span></td>
            <td><span class="badge badge-outline">${b.layout.region}</span></td>
            <td class="muted-text">[${b.bbox.join(", ")}]</td>
          </tr>
        `;
      })
      .join("");

    // Attach Row Hover Listeners
    document.querySelectorAll("#ocrTableBody tr").forEach((row) => {
      const id = row.getAttribute("data-id");
      row.addEventListener("mouseenter", () => highlightBlock(id));
      row.addEventListener("mouseleave", () => unhighlightBlock(id));
    });
  }

  // --- Two-Way Highlight Handlers ---
  function highlightBlock(id) {
    // 1. Highlight SVG Box
    const svgGroup = svgOverlay.querySelector(`.bbox-group[data-id="${id}"]`);
    if (svgGroup) svgGroup.classList.add("highlighted");

    // 2. Highlight Table Row
    const tr = document.getElementById(`row_${id}`);
    if (tr) {
      tr.classList.add("highlighted");
      tr.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function unhighlightBlock(id) {
    const svgGroup = svgOverlay.querySelector(`.bbox-group[data-id="${id}"]`);
    if (svgGroup) svgGroup.classList.remove("highlighted");

    const tr = document.getElementById(`row_${id}`);
    if (tr) tr.classList.remove("highlighted");
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
});
